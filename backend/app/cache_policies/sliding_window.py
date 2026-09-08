# backend/app/cache_policies/sliding_window.py
"""
Sliding-window + attention-sink eviction policy.

Inspired by StreamingLLM (Xiao et al., 2023) which showed that keeping a
small number of "attention sink" tokens at the start of the sequence (in
addition to a recent window) dramatically improves retrieval compared to a
naive sliding window that drops everything old.

Design
------
The cache stores two groups of tokens:
    1. Sink tokens: the first `num_sink_tokens` tokens of the sequence.
       These are kept forever.  Empirically, early tokens accumulate large
       attention mass ("sink" effect), so dropping them hurts softmax
       normalisation even when their content is irrelevant.
    2. Window tokens: the most recent `window_size` tokens.

Layout of K_stored / V_stored (once the cache is full):
    [sink_0, sink_1, ..., sink_{S-1}, recent_{-W}, ..., recent_{-1}]
    |<---- num_sink_tokens --------->|<---- window_size ----------->|

When a new token arrives and the total (sinks + window) is already at its
maximum, the *oldest window token* (just after the sinks) is dropped.
Sink tokens are never dropped.

The returned `cache_mask` is always all-True over whatever tokens are kept:
eviction is done by *removing rows* from K_stored and V_stored, not by
setting mask entries to False.  This keeps the positions contiguous, which
is required for the causal mask in attention.py to work correctly.

Args:
    window_size (int):      Number of *recent* (non-sink) tokens to keep.
                            Default: 64.
    num_sink_tokens (int):  Number of *initial* tokens to keep forever.
                            Default: 4.  Set to 0 to disable sinks (naive
                            sliding window).

Configuring for the CacheQuake demo
------------------------------------
The UI exposes both parameters as sliders.  Interesting experiments:
    - window_size=32, num_sink_tokens=4  → typical StreamingLLM config
    - window_size=32, num_sink_tokens=0  → naive sliding window (breaks earlier)
    - window_size=512, num_sink_tokens=0 → effectively full cache (for seq ≤ 512)

Memory complexity: O(num_sink_tokens + window_size) — bounded, constant
once the cache is full.
"""

import torch

from .base import CachePolicy


class SlidingWindowPolicy(CachePolicy):
    """StreamingLLM-style: keep first S sink tokens + last W window tokens.

    State per layer:
        _store: dict[int, tuple[Tensor, Tensor]]
            Keyed by layer_idx.  Each value is (K_stored, V_stored) where
            K_stored : float[B, H, T_kept, d_head]
            V_stored : float[B, H, T_kept, d_head]
            T_kept   = min(tokens_seen, num_sink_tokens + window_size)

    State for metrics:
        _tokens_seen:    total tokens processed by layer 0 (across all steps)
        _total_evictions: total rows dropped across all layers all steps
    """

    def __init__(
        self,
        window_size:      int = 64,
        num_sink_tokens:  int = 4,
    ) -> None:
        assert window_size > 0, "window_size must be positive"
        assert num_sink_tokens >= 0, "num_sink_tokens must be non-negative"

        self.window_size     = window_size
        self.num_sink_tokens = num_sink_tokens

        # Per-layer accumulated storage.
        # Updated by update(); read by the transformer on the next forward call.
        self._store: dict[int, tuple[torch.Tensor, torch.Tensor]] = {}

        # Metrics (layer 0 only to avoid double-counting)
        self._tokens_seen:    int = 0
        self._total_evictions: int = 0

    # ------------------------------------------------------------------
    # CachePolicy interface
    # ------------------------------------------------------------------

    def update(
        self,
        step:       int,
        layer_idx:  int,
        k:          torch.Tensor,
        v:          torch.Tensor,
        past_cache: tuple[torch.Tensor, torch.Tensor] | None,
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """Append new tokens and evict oldest window tokens if over budget.

        Args:
            step:       Global generation step index (0-based).
            layer_idx:  Which layer's tensors (0-based).
            k:          float[B, H, T_new, d_head]  — new key vectors.
            v:          float[B, H, T_new, d_head]  — new value vectors.
            past_cache: (K_past, V_past) from the previous call, or None.
                        NOTE: In the simulation runner we pass None here and
                        rely on self._store instead, to avoid the runner
                        needing to track per-layer state itself.  The policy
                        is the single source of truth for what's cached.

        Returns:
            K_stored:   float[B, H, T_kept, d_head]
            V_stored:   float[B, H, T_kept, d_head]
            cache_mask: bool[B, T_kept]   — all True (no masked-out rows)
        """
        B, H, T_new, d_head = k.shape
        budget = self.num_sink_tokens + self.window_size

        # --- 1. Get current accumulated cache for this layer ----------
        if layer_idx in self._store:
            K_acc, V_acc = self._store[layer_idx]
            # Concatenate the new tokens onto the right
            K_acc = torch.cat([K_acc, k], dim=2)  # [B, H, T_acc+T_new, d_head]
            V_acc = torch.cat([V_acc, v], dim=2)
        else:
            # First call for this layer — initialise with new tokens only
            K_acc = k
            V_acc = v

        T_acc = K_acc.shape[2]  # total tokens accumulated so far for this layer

        # --- 2. Evict oldest window tokens if over budget --------------
        # The layout of K_acc right now:
        #   [sink_0..sink_{S-1}, window_start..window_end, new_token_0..new_token_{T_new-1}]
        # If T_acc > budget, we need to drop the oldest non-sink tokens.
        #
        # Specifically: we want to keep indices [0 .. S-1] and
        # [(T_acc - window_size) .. T_acc-1].
        # Anything in between gets dropped.

        evicted_this_call = 0
        if T_acc > budget:
            S = self.num_sink_tokens
            W = self.window_size

            # Indices to keep: sinks first, then the last W tokens.
            # torch.cat on the index dimension
            if S > 0:
                sink_part  = K_acc[:, :, :S, :]           # [B, H, S,   d_head]
                window_part = K_acc[:, :, -W:, :]         # [B, H, W,   d_head]
                K_acc = torch.cat([sink_part, window_part], dim=2)  # [B, H, S+W, d_head]

                sink_v   = V_acc[:, :, :S, :]
                window_v = V_acc[:, :, -W:, :]
                V_acc = torch.cat([sink_v, window_v], dim=2)
            else:
                # No sinks — keep only the last W tokens.
                K_acc = K_acc[:, :, -W:, :]
                V_acc = V_acc[:, :, -W:, :]

            evicted_this_call = T_acc - K_acc.shape[2]

        # --- 3. Persist and collect metrics ---------------------------
        self._store[layer_idx] = (K_acc, V_acc)

        if layer_idx == 0:
            self._tokens_seen    += T_new
            self._total_evictions += evicted_this_call

        # --- 4. Build return values -----------------------------------
        T_kept = K_acc.shape[2]
        # cache_mask is all-True: every stored row is visible to the model.
        # Eviction already happened by removing rows — no False entries needed.
        cache_mask = torch.ones(B, T_kept, dtype=torch.bool, device=k.device)

        return K_acc, V_acc, cache_mask

    def reset(self) -> None:
        """Clear all accumulated state for a new episode."""
        self._store.clear()
        self._tokens_seen     = 0
        self._total_evictions = 0

    def memory_tokens_used(self) -> int:
        """Return the current number of stored K/V token slots.

        Before the cache fills up this grows; once full it equals
        num_sink_tokens + window_size and stays constant.
        """
        if not self._store:
            return 0
        # Use layer 0 as canonical; all layers have the same count.
        K_stored, _ = next(iter(self._store.values()))
        return K_stored.shape[2]

    def policy_info(self) -> dict:
        return {
            "policy":          "sliding_window",
            "window_size":     self.window_size,
            "num_sink_tokens": self.num_sink_tokens,
            "tokens_cached":   self.memory_tokens_used(),
            "tokens_seen":     self._tokens_seen,
            "evictions":       self._total_evictions,
        }
