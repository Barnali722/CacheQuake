# backend/app/cache_policies/sliding_window.py
"""
Sliding-window eviction policy (Day 2–3 implementation).

STUB — not yet implemented.  This file exists to define the contract so
the frontend and test suite can reference the class name before the logic
is written.

What this policy will do
------------------------
A sliding window keeps only the most recent W tokens in the KV cache, where
W is a fixed budget set by the user (configurable in the UI).  When the
cache is full:

    1. The *oldest* stored position is evicted (dropped from K_stored/V_stored).
    2. The new token is appended at the end.
    3. The cache_mask is all-True over the kept window: the model sees a
       *contiguous* recent context.

Visual on a 5-token window (W=5), step 10:
    Stored positions:  [6, 7, 8, 9, 10]   ← indices in the global sequence
    Evicted positions: [0, 1, 2, 3, 4, 5]
    cache_mask:        [T, T, T, T, T]

Expected behaviour on the needle-in-haystack task
--------------------------------------------------
If the needle ("The access code for VAULT_3 is 7291.") falls outside the
window W at the time the question is asked, retrieval accuracy drops to near
zero.  The UI will show the needle position and the window boundary so the
learner can directly observe the failure mode.

Memory complexity: O(W) — bounded, does not grow with sequence length.

Implementation plan
-------------------
- __init__(window_size: int)
- update(): pop index 0 from K_stored/V_stored if T_kept == window_size,
            then append new k, v.
- cache_mask: all-True tensor of length min(T_seen, W).
- reset(): zero out stored tensors and step counter.
- memory_tokens_used(): return window_size (or current occupancy if < W).
"""

from .base import CachePolicy
import torch


class SlidingWindowPolicy(CachePolicy):
    """Keeps the W most recent tokens; evicts everything older.

    NOT YET IMPLEMENTED — raise NotImplementedError on all method calls.
    """

    def __init__(self, window_size: int = 64) -> None:
        self.window_size = window_size

    def update(self, step, layer_idx, k, v, past_cache):
        raise NotImplementedError("SlidingWindowPolicy.update() — Day 2 task")

    def reset(self):
        raise NotImplementedError("SlidingWindowPolicy.reset() — Day 2 task")

    def memory_tokens_used(self) -> int:
        raise NotImplementedError("SlidingWindowPolicy.memory_tokens_used() — Day 2 task")
