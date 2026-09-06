# backend/app/tasks/needle_haystack.py
"""
Synthetic needle-in-haystack data generator for CacheQuake.

Purpose
-------
Produces character-level token sequences suitable for the toy Transformer.
The task is: given a long context containing several hidden "facts", correctly
retrieve the fact mentioned in the final question.

This is the *input/output shape* that defines the whole project.  The cache
policies are evaluated on how well the model retrieves the correct answer
when each policy changes what portion of the context is visible.

Fact format
-----------
Facts are short, templated strings like:
    "the access code for vault 3 is 7291."

(We lowercase everything because our vocabulary only has lowercase letters.)
The question at the end of the sequence is:
    "what is the access code for vault 3?"

Answer extraction: the model is expected to generate the digits immediately
following the " is " substring in the matching fact.

Sequence structure
------------------
  [FILLER] [FACT_0] [FILLER] [FACT_1] [FILLER] ... [FILLER] [QUESTION]

Filler is repeated alphabet-like characters to simulate realistic token
consumption without semantic content.

Public API
----------
    task = NeedleHaystackTask(seed=42)
    episode = task.generate(
        n_facts=3,          # how many facts to inject
        seq_len=256,        # target total sequence length in tokens
        question_target=1,  # which fact (0-indexed) the question asks about
    )

    episode.token_ids       : list[int]          — encoded sequence
    episode.answer          : str                — expected answer string
    episode.fact_positions  : dict[str, int]     — {vault_name: start_token_idx}
    episode.question_start  : int                — token index where question begins
    episode.text            : str                — decoded sequence (human-readable)
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from ..model.vocab import encode, decode, VOCAB_SIZE


# ---------------------------------------------------------------------------
# Vault/fact templates
# ---------------------------------------------------------------------------

# Each fact has a name (used as the key in fact_positions) and a template.
# We have 8 vaults so we can inject up to 8 distinct facts per sequence.
_VAULT_NAMES = [f"vault {i}" for i in range(8)]

def _fact_text(vault_name: str, code: str) -> str:
    """Return the fact string for a given vault and access code."""
    return f"the access code for {vault_name} is {code}."

def _question_text(vault_name: str) -> str:
    """Return the question string for a given vault."""
    return f"what is the access code for {vault_name}?"


# ---------------------------------------------------------------------------
# Filler generation
# ---------------------------------------------------------------------------

def _filler(n_tokens: int, rng: random.Random) -> str:
    """Generate n_tokens characters of pseudo-random filler text.

    Filler uses only lowercase letters and spaces so it encodes cleanly
    into our vocabulary without producing any <unk> tokens.
    The content is not meaningful — its only purpose is to consume token
    budget and push facts apart in the sequence.
    """
    # Produce words of 3-7 chars separated by spaces.
    words: list[str] = []
    total = 0
    while total < n_tokens:
        word_len = rng.randint(3, 7)
        word = "".join(rng.choice("abcdefghijklmnopqrstuvwxyz")
                       for _ in range(word_len))
        words.append(word)
        total += word_len + 1  # +1 for the trailing space
    text = " ".join(words)
    # Trim to exactly n_tokens (or just under, to stay safe)
    return text[:n_tokens]


# ---------------------------------------------------------------------------
# Dataclass for episode outputs
# ---------------------------------------------------------------------------

@dataclass
class NeedleHaystackEpisode:
    """All outputs for one generated needle-in-haystack episode.

    Attributes:
        token_ids:      Encoded sequence as a flat list of ints.
        answer:         Ground-truth answer string (the code digits).
        fact_positions: Maps vault name → start token index for each injected fact.
        question_start: Token index where the question begins.
        text:           Full decoded text (for debugging / UI display).
        vault_codes:    Maps vault name → access code string (ground truth).
    """
    token_ids:      list[int]
    answer:         str
    fact_positions: dict[str, int]
    question_start: int
    text:           str
    vault_codes:    dict[str, str]


# ---------------------------------------------------------------------------
# Task class
# ---------------------------------------------------------------------------

class NeedleHaystackTask:
    """Generates synthetic needle-in-haystack episodes for the toy Transformer.

    Args:
        seed: Random seed for reproducibility.  Two NeedleHaystackTask
              objects with the same seed produce identical episode sequences.
    """

    def __init__(self, seed: int = 42) -> None:
        self._rng = random.Random(seed)

    def generate(
        self,
        n_facts:          int = 3,
        seq_len:          int = 256,
        question_target:  int = 0,
    ) -> NeedleHaystackEpisode:
        """Generate one episode.

        Args:
            n_facts:         Number of distinct facts to inject.  Must be
                             between 1 and 8 (we have 8 vault templates).
            seq_len:         Approximate target total length in tokens.
                             The actual length may be slightly shorter because
                             we fit filler into exact slots.
            question_target: Which fact (0-indexed) the final question asks
                             about.  Must be in range [0, n_facts).

        Returns:
            A NeedleHaystackEpisode with all outputs filled in.

        Raises:
            ValueError: If n_facts > 8 or question_target >= n_facts.
        """
        if n_facts > len(_VAULT_NAMES):
            raise ValueError(
                f"n_facts={n_facts} exceeds the number of vault templates "
                f"({len(_VAULT_NAMES)}).  Reduce n_facts or add more templates."
            )
        if question_target >= n_facts:
            raise ValueError(
                f"question_target={question_target} is out of range for "
                f"n_facts={n_facts}.  Must be in [0, {n_facts - 1}]."
            )

        # --- 1. Assign vaults and generate access codes ------------------
        # Shuffle vaults so different episodes use different subsets.
        vaults = self._rng.sample(_VAULT_NAMES, n_facts)

        # Access codes: 4-digit strings drawn from 1000-9999.
        vault_codes: dict[str, str] = {
            v: str(self._rng.randint(1000, 9999)) for v in vaults
        }

        # The question asks about this vault.
        target_vault = vaults[question_target]
        answer       = vault_codes[target_vault]

        # --- 2. Build fact strings and measure their lengths --------------
        fact_strings: list[str] = [
            _fact_text(v, vault_codes[v]) for v in vaults
        ]
        question_string = _question_text(target_vault)

        fact_lengths     = [len(encode(f)) for f in fact_strings]
        question_length  = len(encode(question_string))

        # --- 3. Budget filler tokens across (n_facts + 1) gaps -----------
        # Layout: [gap_0] [fact_0] [gap_1] [fact_1] ... [fact_n] [gap_n+1] [question]
        total_fact_tokens     = sum(fact_lengths)
        total_non_filler      = total_fact_tokens + question_length
        total_filler_budget   = max(0, seq_len - total_non_filler)

        n_gaps = n_facts + 1
        # Distribute filler tokens across gaps; at least 1 token per gap.
        gap_sizes: list[int] = [max(1, total_filler_budget // n_gaps)] * n_gaps
        remainder = total_filler_budget - sum(gap_sizes)
        # Add any leftover tokens to the first gap (before the first fact)
        gap_sizes[0] += remainder

        # --- 4. Assemble the full text sequence ---------------------------
        parts: list[str]    = []
        fact_positions: dict[str, int] = {}
        current_token_idx = 0

        for gap_idx in range(n_gaps):
            # Filler gap
            filler_text = _filler(gap_sizes[gap_idx], self._rng)
            parts.append(filler_text)
            current_token_idx += len(encode(filler_text))

            if gap_idx < n_facts:
                # Record where this fact starts
                fact_name = vaults[gap_idx]
                fact_positions[fact_name] = current_token_idx

                # Append the fact
                fact_str = fact_strings[gap_idx]
                parts.append(fact_str)
                current_token_idx += len(encode(fact_str))

        # Append the question at the end
        question_start = current_token_idx
        parts.append(question_string)

        # --- 5. Encode the full sequence ----------------------------------
        full_text  = " ".join(parts)
        # Re-compute exact positions in the joined string's encoding
        # (the space separators between parts shift positions slightly).
        # Instead, we build token_ids by encoding parts individually
        # and concatenating, so fact_positions are exact.

        token_ids: list[int] = []
        fact_positions_exact: dict[str, int] = {}
        q_start_exact = 0

        for gap_idx in range(n_gaps):
            filler_encoded = encode(_filler(gap_sizes[gap_idx],
                                            random.Random(self._rng.random())))
            token_ids.extend(filler_encoded)

            if gap_idx < n_facts:
                fact_name = vaults[gap_idx]
                fact_positions_exact[fact_name] = len(token_ids)
                token_ids.extend(encode(fact_strings[gap_idx]))

        q_start_exact = len(token_ids)
        token_ids.extend(encode(question_string))

        return NeedleHaystackEpisode(
            token_ids      = token_ids,
            answer         = answer,
            fact_positions = fact_positions_exact,
            question_start = q_start_exact,
            text           = decode(token_ids),
            vault_codes    = vault_codes,
        )
