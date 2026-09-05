/**
 * api/mockResponses.js
 * __mock: true  ← strip this file and its imports on Day 3 when real backend is ready.
 *
 * Produces realistic fake /simulate responses for all four cache policies.
 * JSON shape is identical to the real backend response (CONTROLS_SPEC §5 / ARCHITECTURE §3).
 * Numbers move in the qualitatively correct direction as budget / seq_len change:
 *   - lower budget  → fewer alive tokens, lower accuracy
 *   - higher seq_len → higher baseline, linear growth under "full" policy
 *   - sliding_window keeps exactly `budget` most-recent tokens alive
 *   - heavy_hitter keeps `budget` highest-score tokens (biased toward needles + recency)
 *   - bdh_recurrent keeps a flat fixed-size state of `budget` tokens (no growth ever)
 *   - full keeps every token, baseline = policy line
 *
 * DO NOT use the PrecomputedBadge visual style on anything from this file.
 * Mock data uses its own "MOCK DATA" label (see __mock flag + MockDataBadge.jsx Day 3+).
 */

// ─── Internal helpers ───────────────────────────────────────────────────────

/** Deterministic pseudo-random based on a seed (avoids flicker on re-render) */
function seededRand(seed) {
  let s = seed;
  return () => {
    s = (s * 1664525 + 1013904223) & 0xffffffff;
    return (s >>> 0) / 0xffffffff;
  };
}

/**
 * Generate needle positions deterministically from numNeedles and seqLen.
 * Needles are spaced evenly but not at the very start or end.
 */
function needlePositions(numNeedles, seqLen) {
  const positions = [];
  const step = Math.floor(seqLen / (numNeedles + 1));
  for (let i = 1; i <= numNeedles; i++) {
    positions.push(i * step);
  }
  return positions;
}

/**
 * Build a per-step cache_size_tokens array of length seqLen.
 * Represents how many tokens are in the KV cache at each generation step.
 */
function buildCacheSizeHistory(policy, budget, seqLen) {
  const history = [];
  for (let step = 1; step <= seqLen; step++) {
    switch (policy) {
      case 'full':
        history.push(step); // grows linearly every step — the core claim
        break;
      case 'sliding_window':
        history.push(Math.min(step, budget)); // ramps up then plateaus at budget
        break;
      case 'heavy_hitter':
        // ramps up, then evicts to budget — slightly above budget for realism
        history.push(step <= budget ? step : budget + Math.floor((step - budget) * 0.05));
        break;
      case 'bdh_recurrent':
        // fixed-size state from step 1 — never grows (the BDH claim)
        history.push(Math.min(step, budget));
        break;
      default:
        history.push(step);
    }
  }
  return history;
}

/**
 * Compute alive_token_indices at the final generation step.
 * Policy-specific survival logic (qualitatively correct, not exact simulation).
 */
function buildAliveIndices(policy, budget, seqLen, needlePos, rand) {
  const allIndices = Array.from({ length: seqLen }, (_, i) => i);

  switch (policy) {
    case 'full':
      // All tokens alive — full cache retains everything
      return allIndices;

    case 'sliding_window': {
      // Keep the last `budget` tokens (StreamingLLM-style window)
      // Plus keep index 0 (attention sink)
      const window = allIndices.slice(Math.max(0, seqLen - budget));
      if (!window.includes(0)) window.unshift(0);
      return window;
    }

    case 'heavy_hitter': {
      // Keep top-`budget` tokens by "attention score" — needles + recency win
      // Score = recency_weight + needle_bonus + noise
      const scores = allIndices.map((idx) => {
        const recency = idx / seqLen;                        // 0→1, recent tokens score higher
        const needleBonus = needlePos.includes(idx) ? 0.6 : 0; // needles are high-score
        const noise = rand() * 0.1;
        return { idx, score: recency + needleBonus + noise };
      });
      scores.sort((a, b) => b.score - a.score);
      return scores
        .slice(0, budget)
        .map((s) => s.idx)
        .sort((a, b) => a - b);
    }

    case 'bdh_recurrent': {
      // Fixed-size state: keeps a spread of tokens (not strictly recency or score)
      // Some interference — even needles may be partially displaced
      const stride = Math.max(1, Math.floor(seqLen / budget));
      const kept = [];
      for (let i = 0; i < seqLen && kept.length < budget; i += stride) {
        kept.push(i);
      }
      // Try to include needles but not guaranteed (interference model)
      needlePos.forEach((np) => {
        if (!kept.includes(np) && rand() > 0.35) {
          kept.push(np);
          if (kept.length > budget) kept.shift(); // displace oldest kept
        }
      });
      return kept.sort((a, b) => a - b);
    }

    default:
      return allIndices;
  }
}

/**
 * Compute accuracy score — fraction of needles the model could retrieve.
 * Depends on whether each needle's token is still alive in the cache.
 */
function buildAccuracyAndAnswers(needlePos, aliveIndices, numNeedles, rand) {
  const groundTruth = needlePos.map((_, i) => `token_fact_${String(i + 1).padStart(2, '0')}`);
  const modelAnswers = needlePos.map((np, i) => {
    if (aliveIndices.includes(np)) {
      // Needle is in cache → model retrieves it correctly (with high probability)
      return rand() < 0.9 ? groundTruth[i] : `token_guess_${String(i + 1).padStart(2, '0')}`;
    } else {
      // Needle evicted → model guesses wrong
      return rand() < 0.15
        ? groundTruth[i] // occasional lucky guess
        : `token_guess_${String(i + 1).padStart(2, '0')}`;
    }
  });

  const correct = modelAnswers.filter((ans, i) => ans === groundTruth[i]).length;
  const accuracyScore = numNeedles > 0 ? correct / numNeedles : 0;

  return { model_answers: modelAnswers, ground_truth_answers: groundTruth, accuracyScore };
}

// ─── Public API ──────────────────────────────────────────────────────────────

/**
 * Generate a mock /simulate response.
 * Shape is IDENTICAL to the real backend response (CONTROLS_SPEC §5).
 *
 * @param {object} params
 * @param {string} params.policy       - cachePolicy value
 * @param {number} params.budget       - budgetSize (ignored for 'full')
 * @param {number} params.seq_len      - sequenceLength
 * @param {number} params.num_needles  - needleCount
 *
 * @returns {SimulateResponse & { __mock: true, __policy: string }}
 * @see CONTROLS_SPEC §5
 */
export function getMockResponse({ policy, budget, seq_len, num_needles }) {
  // __mock flag: easy to grep for on Day 3 cleanup
  const effectiveBudget = policy === 'full' ? seq_len : Math.min(budget, seq_len);
  const rand = seededRand(policy.length * 100 + budget + seq_len * 7 + num_needles * 13);

  const needlePos = needlePositions(num_needles, seq_len);
  const aliveIndices = buildAliveIndices(policy, effectiveBudget, seq_len, needlePos, rand);
  const cacheSizeHistory = buildCacheSizeHistory(policy, effectiveBudget, seq_len);
  const { model_answers, ground_truth_answers, accuracyScore } = buildAccuracyAndAnswers(
    needlePos,
    aliveIndices,
    num_needles,
    rand
  );

  return {
    // ── Real response fields (CONTROLS_SPEC §5) ──────────────────────────
    cache_size_tokens:          aliveIndices.length,
    full_cache_baseline_tokens: seq_len,          // full cache always = seq_len
    alive_token_indices:        aliveIndices,
    model_answers,
    ground_truth_answers,
    accuracy_score:             accuracyScore,

    // ── Extended fields for chart animation (per-step history) ───────────
    // Real backend will also return these; frontend reads them for MemoryChart
    cache_size_history:         cacheSizeHistory,
    baseline_history:           Array.from({ length: seq_len }, (_, i) => i + 1),
    needle_positions:           needlePos,       // convenience — derived from ground truth

    // ── Mock metadata (STRIP on Day 3) ──────────────────────────────────
    __mock:   true,
    __policy: policy,
  };
}

// ─── Precomputed accuracy-vs-budget sweep (mock version) ─────────────────────
// This mocks the data/precomputed/accuracy_vs_budget.json file.
// Display this with PrecomputedBadge (CONTROLS_SPEC §3 placement #1).
// __mock: true — replace with loadAccuracyVsBudget() fetch on Day 3.

/**
 * Generate the full accuracy-vs-budget curve for a given policy and seq_len.
 * In production this comes from data/precomputed/accuracy_vs_budget.json.
 *
 * @param {string} policy
 * @param {number} seq_len
 * @param {number} num_needles
 * @returns {Array<{budget: number, accuracy: number}> & { __mock: true }}
 */
export function getMockAccuracyVsBudgetCurve(policy, seq_len = 128, num_needles = 2) {
  const budgets = [8, 16, 24, 32, 48, 64, 96, 128, 192, 256, 384, 512];
  const curve = budgets
    .filter((b) => b <= seq_len)
    .map((b) => {
      const { accuracy_score } = getMockResponse({
        policy,
        budget: b,
        seq_len,
        num_needles,
      });
      return { budget: b, accuracy: accuracy_score };
    });

  return Object.assign(curve, { __mock: true });
}

// ─── Mock BDH published claims (replaces data/precomputed/bdh_published_claims.json) ─
// Display with PrecomputedBadge, text: "Published result (arXiv:2509.26507) — not reproduced by our team"
// __mock: true — replace with loadBDHPublishedClaims() fetch on Day 3.

export const MOCK_BDH_PUBLISHED_CLAIMS = {
  __mock: true,
  source: 'arXiv:2509.26507 — Kosowski et al., "The Dragon Hatchling"',
  note: 'Published results — not reproduced by our team. Our toy simulator ≠ the BDH model.',
  claims: [
    { label: 'Memory growth', value: 'O(1) — fixed-size synaptic state' },
    { label: 'Context handling', value: 'Fixed-size overwriting state (no append)' },
    { label: 'Update rule', value: 'Hebbian local update — no explicit eviction' },
    { label: 'Forgetting mechanism', value: 'Interference (not eviction)' },
  ],
};
