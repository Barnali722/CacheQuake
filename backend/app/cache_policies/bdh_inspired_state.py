# backend/app/cache_policies/bdh_inspired_state.py
"""
Fixed-size recurrent state — toy layer inspired by the BDH architecture.
(Day 2–3 implementation.)

!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
CRITICAL DISCLAIMER — READ BEFORE TOUCHING THIS FILE
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
This is a TOY LAYER INSPIRED BY the BDH architecture (arXiv:2509.26507,
Pathway Inc.).  It is NOT the real BDH model.

Specifically:
  - We do NOT reproduce BDH's learned associative memory update rules.
  - We do NOT claim equivalence to BDH in any performance sense.
  - BDH is Pathway's own published architecture.  We only cite/explain it
    in the project README and the UI's explainer text.
  - All code comments and docstrings in this file must use the phrase:
    "toy layer inspired by BDH, not BDH itself."

This stub and its eventual implementation exist solely to demonstrate, in an
interactive and simplified way, the *conceptual idea* that a fixed-size state
can eliminate KV-cache growth — a concept BDH formalises rigorously.
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

What this toy layer will do (toy layer inspired by BDH, not BDH itself)
------------------------------------------------------------------------
Unlike the other three policies, this one replaces the growing KV cache with
a FIXED-SIZE associative memory matrix M of shape [state_size, d_head].

On each step, instead of appending a new (k, v) row:
    1. Compute a write key w = f(k_new)   — a simple linear projection.
    2. Compute a write gate  α ∈ [0, 1]   — learned scalar per head.
    3. Update:  M ← α * (w ⊗ v) + (1-α) * M
       where ⊗ denotes an outer product that writes into M, weighted by w.
       (This is a simplified Hopfield-style write, not BDH's exact rule.)
    4. Reading: the model's query Q retrieves from M via Q @ M.T instead of
       attending to explicit past (K, V) rows.

Because M has fixed size (state_size rows), memory never grows.
There is no eviction — old information is *overwritten* probabilistically
by new writes.

Interface adaptation (toy layer inspired by BDH, not BDH itself)
------------------------------------------------------------------
This policy still implements CachePolicy so the simulation loop treats it
uniformly.  However, the (K_stored, V_stored) it returns are the *columns*
of M re-shaped as if they were cached token rows.  The cache_mask is all-True
over state_size positions.  The attention module sees exactly the same
interface as for the other policies.

This adaptation is a simplification.  In a production BDH implementation,
the fixed-size state would be integrated directly into the attention kernel,
not retrofitted on top of a standard attention module.

Expected behaviour on needle-in-haystack
-----------------------------------------
If the needle's key pattern aligns strongly with the write-gate at write time,
the needle's value is retained in M indefinitely regardless of sequence length.
When it does not align, the value is gradually overwritten — demonstrating the
*compression trade-off* in a bounded-memory setting.

Memory complexity: O(state_size) — strictly constant, independent of T.

Implementation plan
-------------------
- __init__(state_size: int, d_head: int, n_heads: int)
- M: float[n_heads, state_size, d_head] — the associative memory matrix.
- update(): compute write key and gate, perform M update, reshape M as
            K_stored/V_stored for compatibility.
- reset(): zero M.
- memory_tokens_used(): return state_size (constant).
"""

from .base import CachePolicy
import torch


class BDHInspiredState(CachePolicy):
    """Fixed-size associative state — toy layer inspired by BDH, not BDH itself.

    NOT YET IMPLEMENTED — raises NotImplementedError on all method calls.
    """

    def __init__(self, state_size: int = 32, d_head: int = 16,
                 n_heads: int = 4) -> None:
        self.state_size = state_size
        self.d_head     = d_head
        self.n_heads    = n_heads
        # M will be initialised in reset()
        self.M: torch.Tensor | None = None

    def update(self, step, layer_idx, k, v, past_cache):
        raise NotImplementedError(
            "BDHInspiredState.update() — Day 2 task "
            "(toy layer inspired by BDH, not BDH itself)"
        )

    def reset(self):
        # Initialise the fixed-size associative memory matrix to zeros.
        self.M = torch.zeros(self.n_heads, self.state_size, self.d_head)

    def memory_tokens_used(self) -> int:
        # The state size is constant — memory never grows.
        return self.state_size
