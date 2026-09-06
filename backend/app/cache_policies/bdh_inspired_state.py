# backend/app/cache_policies/bdh_inspired_state.py
"""
Fixed-size recurrent state — toy layer inspired by BDH, not BDH itself.

!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
CRITICAL DISCLAIMER — READ BEFORE TOUCHING THIS FILE
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
This is a TOY LAYER INSPIRED BY the BDH architecture (arXiv:2509.26507,
"The Dragon Hatchling: The Missing Link between the Transformer and Models
of the Brain", Pathway Inc.).

It is NOT the real BDH model.  Specifically:

  (a) INSPIRATION, NOT REPRODUCTION:
      This toy layer is inspired by BDH's conceptual framing of working
      memory as a fixed-size synaptic/Hebbian associative state that
      overwrites old information rather than appending to a growing cache.

  (b) NOT BDH'S ACTUAL MECHANISM:
      Real BDH uses a scale-free graph of locally interacting "neuron
      particles" with spiking dynamics and learned synaptic update rules.
      We do NOT reproduce any of that.  Our update rule is a hand-designed
      soft outer-product write, not learned, not spiking, not graph-based.

  (c) SPECIFIC SIMPLIFICATIONS vs. REAL BDH:
      1. We use a flat slot array M[n_heads, state_size, d_head] instead
         of a graph topology.
      2. Our write rule is:
             M[h] ← decay * M[h] + (1-decay) * softmax_weights ⊗ v_vec
         where softmax_weights = softmax(M[h] @ k_vec / sqrt(d_head)).
         This is a soft Hopfield-style write, not BDH's spiking update.
      3. We use a fixed scalar decay rather than learned per-synapse gates.
      4. We do not implement BDH's "neuron particle" abstraction at all.

  All code comments and docstrings in this file use the phrase:
  "toy layer inspired by BDH, not BDH itself."

This stub and its implementation exist solely to demonstrate, in an
interactive and simplified way, the *conceptual idea* that a fixed-size
state can eliminate KV-cache growth — a concept BDH formalises rigorously.
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

What this toy layer does (toy layer inspired by BDH, not BDH itself)
----------------------------------------------------------------------
Unlike the other three policies, this one replaces the growing KV cache with
a FIXED-SIZE associative memory matrix M of shape [n_heads, state_size, d_head].

M has `state_size` "slots", each a d_head-dimensional vector.  On each new
token, the policy *writes into* M rather than appending to it:

    Write rule (one head h, one step):
        k_vec = k_new[0, h, 0, :]        # [d_head] — new key vector
        v_vec = v_new[0, h, 0, :]        # [d_head] — new value vector

        # Soft addressing: which slot does this key "belong to"?
        # Slots most similar to k_vec receive the strongest write.
        sim   = M[h] @ k_vec             # [state_size] dot products
        addr  = softmax(sim / sqrt(d_head)) # [state_size] — write weights

        # Exponential moving average update: old content decays, new value
        # is scattered across slots proportional to addr.
        M[h]  = decay * M[h] + (1 - decay) * addr[:, None] * v_vec[None, :]
                                          # stays [state_size, d_head]

    Why this rule?
    - M is always exactly [n_heads, state_size, d_head] regardless of how
      many tokens have been processed.  Memory is O(state_size) — constant.
    - "Overwrites rather than appends": the decay factor shrinks old content
      and the new write replaces it.  Slots accumulate the most recent
      relevant patterns rather than an exact verbatim history.
    - The soft addressing (similarity-weighted write) is the Hebbian element:
      pairs (k, v) that co-occur frequently reinforce the same slot, making
      that slot a "heavy hitter" for that pattern.

Read interface adaptation (toy layer inspired by BDH, not BDH itself)
-----------------------------------------------------------------------
For compatibility with the standard attention module, the policy returns M
reshaped as (K_stored, V_stored) both equal to M.  The attention module then
computes:

    output = softmax(Q @ M.T) @ M

This is query-retrieval from the associative memory — the query selects which
slot to read by similarity, which is the natural read rule for this structure.

This adaptation is a simplification.  In a production BDH implementation, the
fixed-size state would be integrated directly into the attention kernel rather
than retrofitted via the KV-cache interface.

Memory complexity: O(state_size) — strictly constant, independent of T.

Args:
    state_size (int): Number of memory slots.  Default: 32.
    d_head (int):     Dimension of each slot (must match the model's d_head).
    n_heads (int):    Number of attention heads.
    decay (float):    Forgetting factor in [0, 1).  0 = total amnesia each
                      step (only last token visible); ~1 = almost no decay
                      (all tokens equally remembered).  Default: 0.9.
"""

import math
import torch

from .base import CachePolicy


class BDHInspiredState(CachePolicy):
    """Fixed-size associative state — toy layer inspired by BDH, not BDH itself.

    See module docstring for the full disclaimer, update rule, and comparison
    with the real BDH architecture.

    Args:
        state_size: Number of fixed memory slots (default: 32).
        d_head:     Slot dimension — must match the model's d_head (default: 16).
        n_heads:    Number of attention heads (default: 4).
        decay:      Exponential decay factor — how much old content persists
                    each step (default: 0.9).
    """

    def __init__(
        self,
        state_size: int   = 32,
        d_head:     int   = 16,
        n_heads:    int   = 4,
        decay:      float = 0.9,
    ) -> None:
        assert 0.0 <= decay < 1.0, "decay must be in [0, 1)"
        assert state_size > 0, "state_size must be positive"

        self.state_size = state_size
        self.d_head     = d_head
        self.n_heads    = n_heads
        self.decay      = decay
        self._scale     = math.sqrt(d_head)  # denominator for similarity

        # M: the fixed-size associative memory.
        # Shape is CONSTANT at [n_heads, state_size, d_head] forever.
        # Initialised in reset(); reset() is called before each episode.
        self.M: torch.Tensor | None = None

        # Metrics
        self._tokens_seen: int = 0

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
        """Write the new (k, v) into M using the soft Hopfield-style rule.

        Toy layer inspired by BDH, not BDH itself.

        Args:
            step:       Global generation step (0-based).
            layer_idx:  Which layer (0-based).  Each layer has its own copy of M.
            k:          float[B, H, T_new, d_head] — new key vectors.
            v:          float[B, H, T_new, d_head] — new value vectors.
            past_cache: Not used — M is the policy's internal state.
                        Accepted for interface compatibility.

        Returns:
            K_stored = M reshaped : float[B, state_size, d_head]  (B=1 always)
            V_stored = M reshaped : float[B, state_size, d_head]
            cache_mask            : bool[B, state_size]   — all True
        """
        B, H, T_new, d_head = k.shape

        # Each layer has its own M; initialise lazily on first write.
        # (reset() is called before the episode, so M is already zeroed there,
        # but this guard handles the multi-layer case cleanly.)
        if self.M is None:
            self.M = torch.zeros(
                self.n_heads, self.state_size, self.d_head,
                device=k.device,
            )
        elif self.M.device != k.device:
            self.M = self.M.to(k.device)

        # --- Write each new token into M ---------------------------------
        # We process T_new tokens (always 1 in our simulation).
        for t in range(T_new):
            for h in range(H):
                # k_vec : [d_head]  — current key for head h, token t
                k_vec = k[0, h, t, :]
                # v_vec : [d_head]  — current value for head h, token t
                v_vec = v[0, h, t, :]

                # Soft addressing: similarity of each slot to k_vec.
                # sim : [state_size]
                sim  = self.M[h] @ k_vec        # dot products
                addr = torch.softmax(sim / self._scale, dim=0)  # [state_size]

                # Write: scatter v_vec into slots weighted by addr.
                # addr[:, None] * v_vec[None, :] : [state_size, d_head]
                write = addr[:, None] * v_vec[None, :]

                # Exponential moving average: old content decays, new writes in.
                self.M[h] = self.decay * self.M[h] + (1.0 - self.decay) * write
                # M[h] shape stays [state_size, d_head] ✓

        # --- Metrics (layer 0 only to avoid double-counting) -------------
        if layer_idx == 0:
            self._tokens_seen += T_new

        # --- Return M as (K_stored, V_stored) ----------------------------
        # Reshape M from [n_heads, state_size, d_head] to
        # [B=1, n_heads, state_size, d_head] so it matches the attention
        # module's expected kv_cache shape.
        #
        # The attention module will do: softmax(Q @ M.T) @ M
        # = soft-addressed read from the associative memory.
        M_expanded = self.M.unsqueeze(0)  # [1, n_heads, state_size, d_head]
        K_stored   = M_expanded           # same tensor for K and V —
        V_stored   = M_expanded           # attention reads from M directly

        # cache_mask: all True over state_size slots
        cache_mask = torch.ones(B, self.state_size, dtype=torch.bool, device=k.device)

        return K_stored, V_stored, cache_mask

    def reset(self) -> None:
        """Zero the associative memory for a new episode.

        Toy layer inspired by BDH, not BDH itself.
        """
        if self.M is not None:
            self.M.zero_()
        else:
            # First call — create M
            self.M = torch.zeros(self.n_heads, self.state_size, self.d_head)
        self._tokens_seen = 0

    def memory_tokens_used(self) -> int:
        """Return state_size — the fixed number of memory slots.

        This is a *constant* regardless of how many tokens have been processed.
        That is the core point: unlike full_cache, sliding_window, or
        heavy_hitter, the memory footprint of this policy never grows.

        Toy layer inspired by BDH, not BDH itself.
        """
        return self.state_size

    def policy_info(self) -> dict:
        return {
            "policy":      "bdh_inspired_state",
            "state_size":  self.state_size,
            "decay":       self.decay,
            "tokens_seen": self._tokens_seen,
            "note":        (
                "toy layer inspired by BDH, not BDH itself. "
                "memory_tokens_used is constant at state_size."
            ),
        }
