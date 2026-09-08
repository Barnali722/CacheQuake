/**
 * api/client.js
 * Single responsibility: Thin wrapper around the backend API endpoints.
 * All network calls go through this file — components never fetch directly.
 *
 * ADAPTER LAYER (added Day 5 QA):
 *   The backend uses different policy names and a nested response shape.
 *   This file maps frontend → backend names on the way IN, and
 *   normalises backend → frontend shape on the way OUT.
 *   Components and the store see the flat CONTROLS_SPEC shape throughout.
 *
 * Endpoint reference: backend/app/main.py
 * Variable names: CONTROLS_SPEC.md §5
 */

const API_BASE =
  (typeof import.meta !== 'undefined' && import.meta.env?.VITE_API_BASE_URL) ||
  'http://localhost:8000';

// ─── Policy name map: frontend value → backend value ──────────────────────────
// Backend accepts: 'full_cache' | 'sliding_window' | 'heavy_hitter' | 'bdh_inspired_state'
// Frontend uses:   'full'       | 'sliding_window' | 'heavy_hitter' | 'bdh_recurrent'
const POLICY_NAME_MAP = {
  full:          'full_cache',
  sliding_window: 'sliding_window',
  heavy_hitter:  'heavy_hitter',
  bdh_recurrent: 'bdh_inspired_state',
};

// ─── Response normaliser ──────────────────────────────────────────────────────
/**
 * The backend returns:
 *   {
 *     episode:    { fact_positions, answer, ... },
 *     simulation: {
 *       steps: [{ step, visible_token_indices, cache_size_tokens, ... }],
 *       correct, final_answer, ground_truth, policy_info
 *     }
 *   }
 *
 * The frontend store (simulationStore.jsx) and components expect:
 *   {
 *     accuracy_score,           // 0–1 float
 *     cache_size_tokens,        // final cache size
 *     full_cache_baseline_tokens,
 *     cache_size_history,       // per-step cache sizes
 *     baseline_history,         // per-step full-cache sizes (simulated)
 *     alive_token_indices,      // final step's alive tokens
 *     needle_positions,         // where needles are in the sequence
 *     model_answers,            // per-needle model answers
 *     correct_answers,          // per-needle ground truth answers
 *   }
 */
function normaliseSimulateResponse(raw) {
  const sim = raw.simulation;
  const ep  = raw.episode;

  if (!sim || !ep) {
    throw new Error('Unexpected backend response shape — missing simulation or episode fields.');
  }

  const steps = Array.isArray(sim.steps) ? sim.steps : [];
  const seqLen = steps.length;

  // Per-step cache size history (live policy)
  const cache_size_history = steps.map(s => s.cache_size_tokens ?? 0);

  // Baseline = full cache = step index + 1 at each step
  const baseline_history = steps.map((_, i) => i + 1);

  // Final values
  const lastStep = steps[steps.length - 1] ?? {};
  const cache_size_tokens = lastStep.cache_size_tokens ?? 0;
  const full_cache_baseline_tokens = seqLen;

  // Alive token indices — use final step's visible_token_indices
  const alive_token_indices = Array.isArray(lastStep.visible_token_indices)
    ? lastStep.visible_token_indices
    : [];

  // Needle positions from episode fact_positions
  const needle_positions = Array.isArray(ep.fact_positions) ? ep.fact_positions : [];

  // Accuracy: single-question correct/wrong → 0.0 or 1.0
  // If multiple needles, correct is still boolean on the last question
  const accuracy_score = sim.correct ? 1.0 : 0.0;

  // Model answer vs correct answer (single needle per episode currently)
  const model_answers   = [sim.final_answer ?? ''];
  const correct_answers = [sim.ground_truth ?? ''];

  return {
    accuracy_score,
    cache_size_tokens,
    full_cache_baseline_tokens,
    cache_size_history,
    baseline_history,
    alive_token_indices,
    needle_positions,
    model_answers,
    correct_answers,
    // Pass through raw for debugging
    _raw: raw,
  };
}

// ─── Shared fetch helper ───────────────────────────────────────────────────────

async function apiFetch(path, options = {}) {
  let res;
  try {
    res = await fetch(`${API_BASE}${path}`, {
      headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
      ...options,
    });
  } catch (networkErr) {
    throw new Error(
      `Network error — could not reach backend at ${API_BASE}${path}. ` +
      `Is the backend running? (${networkErr.message})`
    );
  }

  if (!res.ok) {
    let body = '';
    try { body = await res.text(); } catch (_) { /* ignore */ }
    throw new Error(
      `API error ${res.status} ${res.statusText} on ${path}` +
      (body ? `: ${body.slice(0, 200)}` : '')
    );
  }

  return res.json();
}

// ─────────────────────────────────────────────────────────────────────────────
// POST /simulate
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Run a full simulation with the given parameters.
 *
 * @param {object} params
 * @param {string} params.policy       - "full"|"sliding_window"|"heavy_hitter"|"bdh_recurrent"
 * @param {number} params.budget       - integer 8–512
 * @param {number} params.seq_len      - integer 32–512
 * @param {number} params.num_needles  - integer 1–5
 *
 * @returns {Promise<SimulateResponse>} - normalised flat shape (CONTROLS_SPEC §5)
 */
export async function simulate(params) {
  // Map frontend policy name → backend policy name
  const backendPolicy = POLICY_NAME_MAP[params.policy] ?? params.policy;

  const raw = await apiFetch('/simulate', {
    method: 'POST',
    body: JSON.stringify({ ...params, policy: backendPolicy }),
  });

  // Normalise nested backend response → flat frontend shape
  return normaliseSimulateResponse(raw);
}

// ─────────────────────────────────────────────────────────────────────────────
// Precomputed data loaders — load JSON files served as static assets
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Load the precomputed accuracy-vs-budget sweep curve.
 * Source: backend/data/precomputed/accuracy_vs_budget.json
 * Falls back to the Vite-proxied backend path.
 * Must be displayed with PrecomputedBadge (CONTROLS_SPEC §3 placement #1).
 */
export async function loadAccuracyVsBudget() {
  try {
    return await apiFetch('/data/precomputed/accuracy_vs_budget.json', { method: 'GET' });
  } catch (_) {
    // Return a minimal fallback so the chart doesn't crash if the file isn't served
    return [];
  }
}

/**
 * Load BDH published claims.
 * Source: backend/data/precomputed/bdh_published_claims.json
 * Must be displayed with PrecomputedBadge (CONTROLS_SPEC §3 placement #2).
 */
export async function loadBDHPublishedClaims() {
  try {
    return await apiFetch('/data/precomputed/bdh_published_claims.json', { method: 'GET' });
  } catch (_) {
    return { claims: [] };
  }
}
