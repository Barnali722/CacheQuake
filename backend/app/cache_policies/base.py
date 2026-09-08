# backend/app/cache_policies/base.py
"""
Abstract base class for all KV-cache policies in CacheQuake.

Every cache policy — full cache, sliding window, heavy-hitter eviction, and
the BDH-inspired toy state — implements this interface.  The Transformer's
forward loop calls it after every step; the policy is the only place that
decides what past K/V tensors remain visible.

Design principle
----------------
The Transformer model is cache-policy-agnostic.  It always returns raw K and
V tensors for the tokens it just processed.  It never decides what to keep.
The policy holds all per-layer state and tells the model what to look at next.

Tensor shapes used in this interface:
    B      = batch size
    H      = number of attention heads
    T_kept = number of tokens *currently stored* in the policy's cache
    d_head = d_model // n_heads

update() contract (per layer, per step):
    - Receives the *newly produced* (k, v) for the tokens in this step.
    - May append them, replace them, compress them, or discard them.
    - Returns:
        K_stored  : float[B, H, T_kept, d_head]
        V_stored  : float[B, H, T_kept, d_head]
        cache_mask: bool[B, T_kept]   — True = this position is visible
    - The returned (K_stored, V_stored) and cache_mask are passed directly
      into the next forward call as kv_cache and cache_mask.

memory_tokens_used() contract:
    - Returns the number of (K, V) token slots currently occupied.
    - This number is streamed to the UI for the live memory-usage bar.
    - For a fixed-size architecture this may be a constant.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
import torch


class CachePolicy(ABC):
    """Abstract interface every KV-cache policy must implement.

    Subclasses must implement:
        update()             — called once per layer per generation step
        reset()              — clear all internal state between episodes
        memory_tokens_used() — return current cache occupancy in tokens
    """

    # ------------------------------------------------------------------
    # Core interface
    # ------------------------------------------------------------------

    @abstractmethod
    def update(
        self,
        step:       int,
        layer_idx:  int,
        k:          torch.Tensor,
        v:          torch.Tensor,
        past_cache: tuple[torch.Tensor, torch.Tensor] | None,
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """Incorporate new K/V tensors and return the updated cache state.

        This method is called once for every (layer, generation step) pair.
        The caller (the simulation loop, not the model) is responsible for
        calling update() on every layer before starting the next forward pass.

        Args:
            step:       Zero-based index of the *current generation step*
                        (not the global token index — those differ once the
                        cache has been prefilled from a prompt).
            layer_idx:  Which Transformer layer produced these tensors (0-indexed).
            k:          float[B, H, T_new, d_head]
                        Raw key tensors for the tokens processed *this step*.
            v:          float[B, H, T_new, d_head]
                        Raw value tensors for the tokens processed *this step*.
            past_cache: The (K_stored, V_stored) tuple returned by the *previous*
                        call to update() for this layer, or None on the first step.

        Returns:
            K_stored:   float[B, H, T_kept, d_head]
                        All key tensors the policy wants the model to attend to.
            V_stored:   float[B, H, T_kept, d_head]
                        Corresponding value tensors.
            cache_mask: bool[B, T_kept]
                        True  = the model may attend to this position.
                        False = this position is masked out (evicted or suppressed).
                        Must have T_kept columns matching K_stored.
        """
        ...

    @abstractmethod
    def reset(self) -> None:
        """Clear all per-episode state.

        Called at the start of each new needle-in-haystack episode so the
        policy begins with a fresh cache.  Subclasses should zero out any
        running statistics (e.g., attention-count accumulators for heavy-hitter
        eviction) as well as stored K/V tensors.
        """
        ...

    @abstractmethod
    def memory_tokens_used(self) -> int:
        """Return the number of KV-token slots currently in use.

        Used exclusively for the live memory-usage metric displayed in the UI.
        For a grow-unbounded policy (FullCache), this is the total tokens seen.
        For a fixed-budget policy, this is the budget size (or less at startup).
        For a fixed-size recurrent state, this is the constant state size.

        Returns:
            An integer >= 0.
        """
        ...

    # ------------------------------------------------------------------
    # Optional hook (no-op default)
    # ------------------------------------------------------------------

    def policy_info(self) -> dict:
        """Return a human-readable summary of the policy's current state.

        The default implementation returns an empty dict.  Subclasses may
        override to expose policy-specific metrics (window size, eviction
        counts, etc.) for the /simulate endpoint response.

        Returns:
            A JSON-serialisable dict.
        """
        return {}
