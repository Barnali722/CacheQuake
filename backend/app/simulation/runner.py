# backend/app/simulation/runner.py
"""
Simulation loop for CacheQuake.

This module is the heart of the backend: it wires together the toy Transformer,
a chosen cache policy, and a needle-in-haystack episode, and runs the forward
pass step-by-step while collecting the per-step observability data the UI needs.

Design: prefill-then-decode
---------------------------
Rather than generating token-by-token for the full sequence, we:
    1. PREFILL: process the full input token sequence in one forward call per
       token (streaming, so the cache policy sees each token individually and
       can decide what to keep).
    2. DECODE: run one greedy decode step at the end (on the question's last
       token) to get the model's predicted answer character.

Why not full autoregressive generation?  The interesting observable in this
demo is *which past tokens are visible to the question token*, not iterative
generation quality.  This approach is simpler, faster to trace live, and makes
the cache-policy effect directly visible at the one decode step that matters.

Per-step data collected
-----------------------
For each prefill step i (processing token_ids[i]):
    - step: int                       — step index (0-based)
    - token_id: int                   — the token processed this step
    - token_char: str                 — human-readable character
    - visible_token_indices: list[int]— global indices of all tokens currently
                                        in the cache (layer 0 as canonical)
    - cache_size_tokens: int          — len(visible_token_indices)
    - cache_size_bytes: int           — cache_size_tokens × BYTES_PER_TOKEN

BYTES_PER_TOKEN formula:
    n_layers × 2 (K+V) × n_heads × d_head × 4 (float32 bytes)
    = 4 × 2 × 4 × 16 × 4 = 2048 bytes per token slot
    (All layers store the same number of tokens, so we multiply once.)
"""

from __future__ import annotations

from dataclasses import dataclass, field

import torch

from ..model.toy_transformer import ToyTransformer
from ..model.vocab import decode
from ..cache_policies.base import CachePolicy
from ..tasks.needle_haystack import NeedleHaystackEpisode


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Number of bytes consumed per cached token slot (one entry across all layers).
# n_layers=4, K+V=2, n_heads=4, d_head=16, float32=4 bytes
BYTES_PER_TOKEN_SLOT: int = 4 * 2 * 4 * 16 * 4   # = 2048


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------

@dataclass
class StepRecord:
    """Observability data for a single prefill step."""
    step:                  int
    token_id:              int
    token_char:            str
    visible_token_indices: list[int]   # global position indices visible in cache
    cache_size_tokens:     int
    cache_size_bytes:      int


@dataclass
class SimulationResult:
    """Full output of one run_episode() call.

    Returned by run_episode() and serialised directly into the /simulate
    response JSON.  All list fields are parallel (same length = episode length).
    """
    # Episode metadata (mirrors NeedleHaystackEpisode fields)
    token_ids:      list[int]
    text:           str
    fact_positions: dict[str, int]   # {vault_name: global_start_token_index}
    question_start: int
    ground_truth:   str              # expected answer string

    # Per-step simulation trace (one record per input token)
    steps: list[StepRecord]

    # Final answer (greedy decode of the last token's logits)
    final_answer:   str
    correct:        bool             # final_answer == ground_truth

    # Policy metadata
    policy_name:    str
    policy_params:  dict
    policy_info:    dict             # from CachePolicy.policy_info()


# ---------------------------------------------------------------------------
# Simulation runner
# ---------------------------------------------------------------------------

def run_episode(
    model:   ToyTransformer,
    policy:  CachePolicy,
    episode: NeedleHaystackEpisode,
    policy_name:   str,
    policy_params: dict,
) -> SimulationResult:
    """Run one needle-in-haystack episode with the given cache policy.

    The function:
        1. Resets the policy (clears any state from a previous episode).
        2. Prefills the model token-by-token, calling policy.update() after
           each token's K/V tensors are returned, and recording step data.
        3. Reads off the model's answer from the logits at the final token.

    Args:
        model:         The shared ToyTransformer instance (must be in eval mode).
        policy:        Any CachePolicy implementation (full_cache, sliding_window, …).
        episode:       A NeedleHaystackEpisode from NeedleHaystackTask.generate().
        policy_name:   String name of the policy (for the response JSON).
        policy_params: Dict of policy constructor kwargs (for the response JSON).

    Returns:
        A SimulationResult with the full step trace and final answer.
    """
    # --- Setup -----------------------------------------------------------
    policy.reset()

    token_ids: list[int] = episode.token_ids
    n_tokens = len(token_ids)

    # past_caches[i] = (K_stored, V_stored) for layer i; None before first step.
    past_caches: list[tuple[torch.Tensor, torch.Tensor] | None] = [None] * model.n_layers
    cache_masks: list[torch.Tensor | None] = [None] * model.n_layers

    # Track which *global* token indices are currently in the cache.
    # The policy controls which rows survive; we track the corresponding
    # global positions here so the frontend can colour the input sequence.
    #
    # We use a list-of-lists: one list per layer-0 entry in K_stored,
    # mapping stored-row-index → global token index.
    # After every eviction we recompute this mapping.
    visible_indices: list[int] = []  # global token indices currently stored (layer 0)

    steps: list[StepRecord] = []

    # --- Token-by-token prefill ------------------------------------------
    with torch.no_grad():
        for global_pos, tok_id in enumerate(token_ids):

            # Shape: [B=1, T=1] — one token per step
            ids_tensor = torch.tensor([[tok_id]], dtype=torch.long)

            # Forward pass: the model attends to past_caches using cache_masks.
            logits, present_caches = model(
                ids_tensor,
                past_caches=past_caches,
                cache_masks=cache_masks,
            )
            # logits shape: [1, 1, vocab_size]
            # present_caches: list of n_layers (k_new, v_new), each [1, H, 1, d_head]

            # --- Call policy.update() for every layer --------------------
            new_past_caches: list = []
            new_cache_masks: list = []

            for layer_idx in range(model.n_layers):
                k_new, v_new = present_caches[layer_idx]

                K_stored, V_stored, mask = policy.update(
                    step      = global_pos,
                    layer_idx = layer_idx,
                    k         = k_new,
                    v         = v_new,
                    past_cache= past_caches[layer_idx],
                )
                new_past_caches.append((K_stored, V_stored))
                new_cache_masks.append(mask)

            past_caches = new_past_caches
            cache_masks = new_cache_masks

            # --- Update visible_indices for layer 0 ----------------------
            # Four policy types need different treatment:
            #
            # 1. FullCachePolicy / SlidingWindowPolicy:
            #    The runner mirrors the eviction logic by tracking the same
            #    sink+window structure (existing approach).
            #
            # 2. HeavyHitterPolicy:
            #    The policy tracks which global positions it keeps in
            #    self._global_indices (updated inside policy.update()).
            #    We read that directly — no need to mirror score-ranking logic.
            #
            # 3. BDHInspiredState:
            #    No stored token rows — only state_size fixed memory slots.
            #    Return slot indices 0..state_size-1 as visible_token_indices.
            #    The frontend renders these as a fixed-size memory bar.

            T_kept = past_caches[0][0].shape[2]  # K_stored rows for layer 0

            if hasattr(policy, "_global_indices"):
                # HeavyHitterPolicy: read the ground-truth index list directly.
                visible_indices = list(policy._global_indices)

            elif hasattr(policy, "state_size") and not hasattr(policy, "window_size"):
                # BDHInspiredState: fixed slot indices, not token positions.
                visible_indices = list(range(T_kept))   # [0, 1, ..., state_size-1]

            else:
                # FullCachePolicy / SlidingWindowPolicy: mirror eviction logic.
                visible_indices.append(global_pos)

                if len(visible_indices) > T_kept:
                    n_sink = getattr(policy, "num_sink_tokens", 0)
                    window = T_kept - n_sink
                    if n_sink > 0:
                        visible_indices = (
                            visible_indices[:n_sink]
                            + visible_indices[-window:]
                        )
                    else:
                        visible_indices = visible_indices[-T_kept:]

            # Safety: visible_indices length must match T_kept
            assert len(visible_indices) == T_kept, (
                f"Step {global_pos}: visible_indices len {len(visible_indices)} "
                f"!= T_kept {T_kept}"
            )

            # --- Record step data ----------------------------------------
            steps.append(StepRecord(
                step                  = global_pos,
                token_id              = tok_id,
                token_char            = decode([tok_id]),
                visible_token_indices = list(visible_indices),   # snapshot copy
                cache_size_tokens     = T_kept,
                cache_size_bytes      = T_kept * BYTES_PER_TOKEN_SLOT,
            ))

    # --- Final answer: greedy argmax at the last token's logits ----------
    # logits shape: [1, 1, vocab_size] — the last token processed
    last_logits = logits[0, 0, :]          # [vocab_size]
    predicted_id = int(last_logits.argmax().item())
    final_answer_char = decode([predicted_id])

    # The model's "answer" is a single character (the first character of the
    # expected numeric code).  This is intentional: we're demonstrating that
    # the model can *attend to* the fact, not that it can generate a full
    # answer.  Correctness is measured by whether the predicted character
    # matches the first character of the ground-truth code.
    ground_truth_first_char = episode.answer[0] if episode.answer else ""
    correct = final_answer_char == ground_truth_first_char

    return SimulationResult(
        token_ids      = episode.token_ids,
        text           = episode.text,
        fact_positions = episode.fact_positions,
        question_start = episode.question_start,
        ground_truth   = episode.answer,
        steps          = steps,
        final_answer   = final_answer_char,
        correct        = correct,
        policy_name    = policy_name,
        policy_params  = policy_params,
        policy_info    = policy.policy_info(),
    )
