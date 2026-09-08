# backend/app/cache_policies/full_cache.py
"""
Full-cache policy: keep every K/V tensor ever produced.

This is the baseline — equivalent to a standard autoregressive Transformer
that never evicts anything.  Memory grows by exactly 1 token per generation
step, per layer.

Why this is useful as a baseline:
    - It produces the *highest possible retrieval accuracy* for any task
      where the needle is still within max_seq_len.
    - Its memory usage is the upper bound that eviction policies try to reduce.
    - In the CacheQuake UI, learners will see the memory bar grow linearly
      here, then compare it to the bounded bars of the other policies.

Limitations (the point the UI teaches):
    - Memory is O(T) in the number of tokens seen.
    - At max_seq_len=512 and d_model=64 with 4 layers, this is:
        4 layers × 2 (K+V) × 512 × 64 floats × 4 bytes ≈ 1 MB (tiny here,
        but the *growth pattern* is what matters at real model scale).
"""

import torch

from .base import CachePolicy


class FullCachePolicy(CachePolicy):
    """Trivial KV-cache: append every new token, never evict.

    State:
        _total_tokens (int): running count of tokens appended across all
            update() calls for layer 0 (used by memory_tokens_used()).
            All layers will have the same count, so we only track layer 0.
    """

    def __init__(self) -> None:
        self._total_tokens: int = 0  # grows monotonically, never resets except via reset()

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
        """Append new K/V tensors to the running cache.

        Args:
            step:       Current generation step (unused by full-cache policy —
                        included to satisfy the interface).
            layer_idx:  Which layer's tensors these are.
            k:          float[B, H, T_new, d_head]  — new key tensors.
            v:          float[B, H, T_new, d_head]  — new value tensors.
            past_cache: (K_past, V_past) or None on the first call.

        Returns:
            K_stored:   float[B, H, T_past + T_new, d_head]
            V_stored:   float[B, H, T_past + T_new, d_head]
            cache_mask: bool[B, T_past + T_new]  — all True (nothing evicted)
        """
        B, H, T_new, d_head = k.shape

        if past_cache is None:
            # First call for this layer in this episode — nothing to concatenate.
            K_stored = k
            V_stored = v
        else:
            K_past, V_past = past_cache   # [B, H, T_past, d_head]
            K_stored = torch.cat([K_past, k], dim=2)  # [B, H, T_past+T_new, d_head]
            V_stored = torch.cat([V_past, v], dim=2)

        T_kept = K_stored.shape[2]

        # All positions are visible — no eviction.
        cache_mask = torch.ones(B, T_kept, dtype=torch.bool, device=k.device)

        # Track total tokens for layer 0 only to avoid double-counting layers.
        if layer_idx == 0:
            self._total_tokens += T_new

        return K_stored, V_stored, cache_mask

    def reset(self) -> None:
        """Clear the token counter between episodes."""
        self._total_tokens = 0

    def memory_tokens_used(self) -> int:
        """Return the total number of cached token slots."""
        return self._total_tokens

    def policy_info(self) -> dict:
        return {
            "policy":        "full_cache",
            "tokens_cached": self._total_tokens,
            "evictions":     0,
        }
