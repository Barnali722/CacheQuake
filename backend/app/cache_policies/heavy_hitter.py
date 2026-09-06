# backend/app/cache_policies/heavy_hitter.py
"""
Heavy-hitter eviction policy (Day 2–3 implementation).

STUB — not yet implemented.  This file exists to define the contract so
the frontend and test suite can reference the class name before the logic
is written.

What this policy will do
------------------------
Heavy-hitter eviction (inspired by the H2O paper, IIRC NeurIPS 2023) keeps
the K most *important* tokens rather than the K most *recent*.  Importance
is measured by accumulating attention scores across heads and steps: tokens
that receive high attention mass frequently are "heavy hitters" and are kept;
low-attention tokens are evicted.

Algorithm sketch:
    - Maintain a score vector s of shape [T_seen] initialised to 0.
    - After each forward pass, add the attention weights (summed over heads)
      to s for each key position.
    - When T_seen > budget:
        1. Find the (T_seen - budget) lowest-scoring positions.
        2. Drop those rows from K_stored and V_stored.
        3. Zero out their score entries.
    - cache_mask: all-True over the surviving positions.

Note: this requires access to the attention weight matrix from the forward
pass.  The MultiHeadAttention module will need a small addition to optionally
return the softmax weights — this is planned for Day 2 alongside this policy.

Expected behaviour on needle-in-haystack
-----------------------------------------
If the needle is attended to by at least some attention heads during the
context-processing phase, it accumulates a high score and survives eviction
even when positioned far from the question.  This often outperforms
sliding-window on recall, which the UI will make visible.

Memory complexity: O(budget) — bounded, does not grow with sequence length.

Implementation plan
-------------------
- __init__(budget: int)
- update(): accumulate attention scores, evict low scorers when over budget.
- cache_mask: all-True tensor of length min(T_seen, budget).
- reset(): zero score accumulators, clear stored K/V.
- memory_tokens_used(): return budget (or current occupancy if < budget).
"""

from .base import CachePolicy
import torch


class HeavyHitterPolicy(CachePolicy):
    """Keeps the B highest-attention-score tokens; evicts the rest.

    NOT YET IMPLEMENTED — raises NotImplementedError on all method calls.
    """

    def __init__(self, budget: int = 64) -> None:
        self.budget = budget

    def update(self, step, layer_idx, k, v, past_cache):
        raise NotImplementedError("HeavyHitterPolicy.update() — Day 2 task")

    def reset(self):
        raise NotImplementedError("HeavyHitterPolicy.reset() — Day 2 task")

    def memory_tokens_used(self) -> int:
        raise NotImplementedError("HeavyHitterPolicy.memory_tokens_used() — Day 2 task")
