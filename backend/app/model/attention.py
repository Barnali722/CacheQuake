# backend/app/model/attention.py
"""
Multi-head causal self-attention for CacheQuake's toy Transformer.

Key design goal — cache-policy interception hook
------------------------------------------------
Every cache policy needs to control *which past K/V entries are visible*
to the current step, without touching the attention math itself.

We achieve this with a single optional boolean tensor, ``cache_mask``:

    cache_mask : bool[B, T_past]
        True  = this past position is visible   (attend to it)
        False = this past position is evicted   (mask it out)

Cache policies set False on positions they have evicted.  The attention
module never decides what to keep — it just obeys the mask it receives.

Tensor shapes (throughout this file):
    B        = batch size
    T        = number of new tokens in this forward call (query length)
    T_past   = number of cached tokens (key/value length)
    H        = number of attention heads   (n_heads)
    d_model  = total model dimension       (e.g. 64)
    d_head   = d_model // n_heads          (e.g. 16 for H=4, d_model=64)
"""

import math
import torch
import torch.nn as nn
import torch.nn.functional as F


class MultiHeadAttention(nn.Module):
    """Standard multi-head causal self-attention with an optional cache mask.

    Args:
        d_model: Total model dimension (must be divisible by n_heads).
        n_heads: Number of attention heads.

    Forward inputs:
        x          : float[B, T, d_model]       — query/key/value source
        kv_cache   : optional tuple (K_past, V_past)
                       K_past : float[B, H, T_past, d_head]
                       V_past : float[B, H, T_past, d_head]
        cache_mask : optional bool[B, T_past]
                       True  = attend to this cached position
                       False = treat as evicted (−inf before softmax)

    Forward outputs:
        out : float[B, T, d_model]     — attended output
        k   : float[B, H, T, d_head]  — raw K for the *current* tokens only
        v   : float[B, H, T, d_head]  — raw V for the *current* tokens only

    The cache policy receives (k, v) after each forward call and decides
    what to store.  It then passes the stored tensors as kv_cache and its
    own boolean cache_mask on the next call.
    """

    def __init__(self, d_model: int, n_heads: int) -> None:
        super().__init__()

        assert d_model % n_heads == 0, (
            f"d_model ({d_model}) must be divisible by n_heads ({n_heads})"
        )

        self.n_heads = n_heads
        self.d_head  = d_model // n_heads   # 16 when d_model=64, n_heads=4
        self.d_model = d_model
        self.scale   = math.sqrt(self.d_head)  # denominator in softmax

        # Single fused projection: produces Q, K, V in one matrix multiply.
        # Weight shape: [d_model, 3 * d_model]
        # We split the output 3-ways along dim=-1 after projection.
        self.qkv_proj = nn.Linear(d_model, 3 * d_model, bias=False)

        # Output projection back to d_model
        self.out_proj = nn.Linear(d_model, d_model, bias=False)

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------

    def _split_heads(self, x: torch.Tensor) -> torch.Tensor:
        """Reshape [B, T, d_model] -> [B, H, T, d_head]."""
        B, T, _ = x.shape
        # view into (B, T, H, d_head) then transpose to (B, H, T, d_head)
        return x.view(B, T, self.n_heads, self.d_head).transpose(1, 2)

    def _merge_heads(self, x: torch.Tensor) -> torch.Tensor:
        """Reshape [B, H, T, d_head] -> [B, T, d_model]."""
        B, H, T, d_head = x.shape
        # transpose back to (B, T, H, d_head) then flatten last two dims
        return x.transpose(1, 2).contiguous().view(B, T, H * d_head)

    # ------------------------------------------------------------------
    # forward
    # ------------------------------------------------------------------

    def forward(
        self,
        x: torch.Tensor,
        kv_cache: tuple[torch.Tensor, torch.Tensor] | None = None,
        cache_mask: torch.Tensor | None = None,
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """Run multi-head causal attention.

        See class docstring for full shape documentation.
        """
        B, T, _ = x.shape  # batch, new-token count, model dim

        # --- 1. Project to Q, K, V for the current tokens ---------------
        # qkv : [B, T, 3 * d_model]
        qkv = self.qkv_proj(x)
        # Split along the last dimension into three equal chunks
        q, k, v = qkv.chunk(3, dim=-1)   # each: [B, T, d_model]

        # Split into multiple heads
        q = self._split_heads(q)  # [B, H, T, d_head]
        k = self._split_heads(k)  # [B, H, T, d_head]
        v = self._split_heads(v)  # [B, H, T, d_head]

        # --- 2. Concatenate with cached K/V if provided ------------------
        # k_full, v_full include both the cache and the current tokens.
        if kv_cache is not None:
            k_past, v_past = kv_cache         # [B, H, T_past, d_head] each
            k_full = torch.cat([k_past, k], dim=2)  # [B, H, T_past+T, d_head]
            v_full = torch.cat([v_past, v], dim=2)
        else:
            k_full = k   # [B, H, T, d_head]
            v_full = v

        T_full = k_full.shape[2]   # total key/value length (past + current)

        # --- 3. Build the attention bias matrix --------------------------
        # We use an additive bias: 0 for allowed positions, −∞ for masked.
        # Shape: [B, H, T, T_full]  (broadcast over H is fine)

        # 3a. Causal mask: token i cannot attend to token j > i
        # We create this for the full T×T_full rectangle.
        # Row i corresponds to query position (T_past + i) in the sequence.
        T_past = T_full - T
        # query positions in the global sequence: [T_past, T_past+1, ..., T_full-1]
        query_pos = torch.arange(T_past, T_full, device=x.device)  # [T]
        # key positions: [0, 1, ..., T_full-1]
        key_pos   = torch.arange(T_full,          device=x.device)  # [T_full]
        # causal: q_pos[i] >= k_pos[j]  →  allowed
        causal_ok = query_pos[:, None] >= key_pos[None, :]  # [T, T_full] bool
        causal_bias = torch.where(causal_ok, 0.0, float("-inf"))  # [T, T_full]

        # 3b. Cache-eviction mask: only applied to the *past* portion.
        # cache_mask : bool[B, T_past]  — True = keep, False = evict
        if cache_mask is not None and T_past > 0:
            # Expand to [B, 1, 1, T_past] so it broadcasts over H and T.
            eviction_bias = torch.where(
                cache_mask[:, None, None, :],  # [B, 1, 1, T_past]
                torch.zeros(1, device=x.device),
                torch.full((1,), float("-inf"), device=x.device),
            )  # [B, 1, 1, T_past]

            # Current tokens are never evicted — pad with zeros on the right.
            current_bias = torch.zeros(B, 1, 1, T, device=x.device)
            # [B, 1, 1, T_full]
            eviction_full = torch.cat([eviction_bias, current_bias], dim=-1)
        else:
            eviction_full = 0.0  # scalar zero = no eviction masking

        # 3c. Combine: broadcast causal_bias [T, T_full] with eviction [B,1,1,T_full]
        attn_bias = causal_bias[None, None, :, :] + eviction_full  # [B, 1, T, T_full]

        # --- 4. Scaled dot-product attention -----------------------------
        # scores : [B, H, T, T_full]
        scores = torch.matmul(q, k_full.transpose(-2, -1)) / self.scale
        scores = scores + attn_bias               # apply combined mask
        weights = F.softmax(scores, dim=-1)       # [B, H, T, T_full]
        attended = torch.matmul(weights, v_full)  # [B, H, T, d_head]

        # --- 5. Merge heads and project output ---------------------------
        out = self._merge_heads(attended)   # [B, T, d_model]
        out = self.out_proj(out)            # [B, T, d_model]

        # Return raw K and V for *current tokens only* so the cache layer
        # can store them.  (We don't return k_full/v_full — the policy
        # manages concatenation itself so it can interleave eviction logic.)
        return out, k, v
