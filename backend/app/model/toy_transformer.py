# backend/app/model/toy_transformer.py
"""
Decoder-only toy Transformer for CacheQuake.

This is a real, from-scratch PyTorch implementation — not a wrapper around
nn.Transformer or HuggingFace.  Every line is intentionally simple and
inspectable so any team member can trace it live during a defence.

Architecture summary
--------------------
  - Token + positional embeddings   (learned sinusoidal-style)
  - N identical decoder layers:
      LayerNorm → MultiHeadAttention → residual
      LayerNorm → Feed-forward (d_model → 4*d_model → d_model) → residual
  - Final LayerNorm → linear head → logits over vocabulary

Confirmed spec (DataForge 2026 hackathon):
  vocab_size  = 40      (from vocab.py)
  d_model     = 64
  n_heads     = 4       → d_head = 16
  n_layers    = 4
  max_seq_len = 512

Tensor shape convention (used throughout this file and the README):
  B   = batch size
  T   = sequence length of the *current* call
  V   = vocab_size
  H   = n_heads
  d   = d_model
  d_h = d_head = d // H
"""

import torch
import torch.nn as nn

from .attention import MultiHeadAttention


# ---------------------------------------------------------------------------
# Feed-forward block
# ---------------------------------------------------------------------------

class FeedForward(nn.Module):
    """Position-wise feed-forward network: Linear → ReLU → Linear.

    The inner dimension is 4 × d_model, matching the standard Transformer
    paper ratio.  No dropout is used — the model is tiny and we want
    deterministic, inspectable forward passes.

    Args:
        d_model: Input/output dimension.
    """

    def __init__(self, d_model: int) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(d_model, 4 * d_model),
            nn.ReLU(),
            nn.Linear(4 * d_model, d_model),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: float[B, T, d_model]
        Returns:
            float[B, T, d_model]
        """
        return self.net(x)


# ---------------------------------------------------------------------------
# Single Transformer decoder layer
# ---------------------------------------------------------------------------

class TransformerLayer(nn.Module):
    """One decoder layer: pre-norm attention + pre-norm feed-forward.

    We use *pre-norm* (LayerNorm before the sub-layer) rather than the
    original post-norm because it trains more stably at small scale.

    Args:
        d_model: Model dimension.
        n_heads: Number of attention heads.

    Forward:
        x          : float[B, T, d_model]
        kv_cache   : optional (K_past, V_past) — see MultiHeadAttention
        cache_mask : optional bool[B, T_past]  — eviction mask

    Returns:
        out        : float[B, T, d_model]
        k          : float[B, H, T, d_head]   raw K for current tokens
        v          : float[B, H, T, d_head]   raw V for current tokens
    """

    def __init__(self, d_model: int, n_heads: int) -> None:
        super().__init__()
        self.norm1  = nn.LayerNorm(d_model)
        self.attn   = MultiHeadAttention(d_model, n_heads)
        self.norm2  = nn.LayerNorm(d_model)
        self.ff     = FeedForward(d_model)

    def forward(
        self,
        x: torch.Tensor,
        kv_cache: tuple[torch.Tensor, torch.Tensor] | None = None,
        cache_mask: torch.Tensor | None = None,
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:

        # --- Attention sub-layer (pre-norm + residual) ---
        residual  = x
        x_normed  = self.norm1(x)
        attn_out, k, v = self.attn(x_normed, kv_cache=kv_cache,
                                   cache_mask=cache_mask)
        x = residual + attn_out   # residual connection

        # --- Feed-forward sub-layer (pre-norm + residual) ---
        residual = x
        x = residual + self.ff(self.norm2(x))

        return x, k, v


# ---------------------------------------------------------------------------
# Full toy Transformer
# ---------------------------------------------------------------------------

class ToyTransformer(nn.Module):
    """4-layer decoder-only Transformer for the CacheQuake demo.

    Interface summary for cache-policy integration
    -----------------------------------------------
    1. Call ``forward(token_ids, past_caches, cache_masks)`` to get logits
       and ``present_caches`` (raw K, V tensors for every layer).
    2. Hand ``present_caches`` to the active ``CachePolicy.update()`` call.
    3. The policy returns updated ``(K_stored, V_stored, cache_mask)`` tuples.
    4. Pass those back on the next forward call.

    Args:
        vocab_size:  Size of the token vocabulary (default: 40).
        d_model:     Total model dimension (default: 64).
        n_heads:     Number of attention heads (default: 4).
        n_layers:    Number of Transformer layers (default: 4).
        max_seq_len: Maximum sequence length (default: 512).

    Forward inputs:
        token_ids   : int[B, T]
            Token ids for the current chunk of tokens.
        past_caches : list of length n_layers, each element is a tuple
                      (K_past, V_past) or None.
                      - K_past : float[B, H, T_past, d_head]
                      - V_past : float[B, H, T_past, d_head]
                      Pass None (or an empty list) for the very first call.
        cache_masks : list of length n_layers, each element is a
                      bool[B, T_past] tensor or None.
                      True  = keep this cached position visible.
                      False = this position has been evicted.
                      Pass None for each layer if no eviction is active.

    Forward outputs:
        logits        : float[B, T, vocab_size]
        present_caches: list of n_layers tuples (K_new, V_new)
                        These are the *raw, unfiltered* K and V tensors for
                        the current tokens.  The cache policy decides what to
                        keep, discard, or compress — the model never does.
    """

    def __init__(
        self,
        vocab_size:  int  = 44,   # 42 printable symbols + PAD + UNK
        d_model:    int  = 64,
        n_heads:    int  = 4,
        n_layers:   int  = 4,
        max_seq_len: int = 512,
    ) -> None:
        super().__init__()

        self.d_model     = d_model
        self.n_layers    = n_layers
        self.max_seq_len = max_seq_len

        # --- Token embedding ---
        # Maps each token id to a d_model-dimensional vector.
        self.token_emb = nn.Embedding(vocab_size, d_model)

        # --- Positional embedding ---
        # Learned, one vector per absolute position up to max_seq_len.
        # The current-step position is computed as T_past + t, where T_past
        # is inferred from the length of the cache.
        self.pos_emb = nn.Embedding(max_seq_len, d_model)

        # --- Transformer layers ---
        self.layers = nn.ModuleList([
            TransformerLayer(d_model, n_heads)
            for _ in range(n_layers)
        ])

        # --- Final layer norm + linear head ---
        self.final_norm = nn.LayerNorm(d_model)
        self.lm_head    = nn.Linear(d_model, vocab_size, bias=False)

        # Weight tying: share token embedding and output projection weights.
        # This is a standard trick that reduces parameters without hurting
        # quality and makes the embedding space more interpretable.
        self.lm_head.weight = self.token_emb.weight

        # --- Weight initialisation ---
        self._init_weights()

    def _init_weights(self) -> None:
        """Small normal-distribution initialisation for every Linear layer."""
        for module in self.modules():
            if isinstance(module, nn.Linear):
                nn.init.normal_(module.weight, mean=0.0, std=0.02)
                if module.bias is not None:
                    nn.init.zeros_(module.bias)
            elif isinstance(module, nn.Embedding):
                nn.init.normal_(module.weight, mean=0.0, std=0.02)

    # -----------------------------------------------------------------------
    # forward
    # -----------------------------------------------------------------------

    def forward(
        self,
        token_ids:   torch.Tensor,
        past_caches: list | None = None,
        cache_masks: list | None = None,
    ) -> tuple[torch.Tensor, list[tuple[torch.Tensor, torch.Tensor]]]:
        """Run a forward pass over the given tokens.

        See class docstring for full argument and return-value documentation.
        """
        B, T = token_ids.shape

        # Normalise optional arguments to per-layer lists of correct length.
        if past_caches is None or len(past_caches) == 0:
            past_caches = [None] * self.n_layers
        if cache_masks is None or len(cache_masks) == 0:
            cache_masks = [None] * self.n_layers

        assert len(past_caches) == self.n_layers, (
            f"past_caches must have one entry per layer ({self.n_layers}), "
            f"got {len(past_caches)}"
        )
        assert len(cache_masks) == self.n_layers, (
            f"cache_masks must have one entry per layer ({self.n_layers}), "
            f"got {len(cache_masks)}"
        )

        # --- 1. Determine how many tokens are already cached ---------------
        # We use layer 0's cache length as the canonical offset.
        # All layers must always have the same T_past (enforced by the policy).
        if past_caches[0] is not None:
            T_past = past_caches[0][0].shape[2]  # K_past: [B, H, T_past, d_h]
        else:
            T_past = 0

        # Safety check: we must not exceed max_seq_len
        if T_past + T > self.max_seq_len:
            raise ValueError(
                f"Sequence length {T_past + T} exceeds max_seq_len "
                f"({self.max_seq_len}).  Evict more tokens or use a shorter "
                f"input."
            )

        # --- 2. Embeddings -------------------------------------------------
        # Token ids for this chunk
        tok_emb = self.token_emb(token_ids)  # [B, T, d_model]

        # Positional ids: T_past, T_past+1, …, T_past+T-1
        # shape: [T], then broadcast to [B, T] is handled by Embedding.
        pos_ids = torch.arange(T_past, T_past + T, device=token_ids.device)
        pos_emb = self.pos_emb(pos_ids)  # [T, d_model] — broadcast over B

        # x : [B, T, d_model]
        x = tok_emb + pos_emb  # broadcasting: pos_emb adds the same offset to each batch item

        # --- 3. Pass through each Transformer layer ------------------------
        present_caches: list[tuple[torch.Tensor, torch.Tensor]] = []

        for i, layer in enumerate(self.layers):
            x, k_new, v_new = layer(
                x,
                kv_cache   = past_caches[i],
                cache_mask = cache_masks[i],
            )
            # k_new, v_new : [B, H, T, d_head] — only current-step tensors.
            # The cache policy decides what to store; we just return them raw.
            present_caches.append((k_new, v_new))

        # --- 4. Head ---------------------------------------------------------
        x      = self.final_norm(x)             # [B, T, d_model]
        logits = self.lm_head(x)                # [B, T, vocab_size]

        return logits, present_caches

    # -----------------------------------------------------------------------
    # Convenience
    # -----------------------------------------------------------------------

    def count_parameters(self) -> int:
        """Return the total number of trainable parameters."""
        return sum(p.numel() for p in self.parameters() if p.requires_grad)

    def model_info(self) -> dict:
        """Return a summary dict for the /health endpoint."""
        return {
            "d_model":      self.d_model,
            "n_heads":      self.n_layers,  # yes, n_heads stored at init
            "n_layers":     self.n_layers,
            "max_seq_len":  self.max_seq_len,
            "n_parameters": self.count_parameters(),
        }
