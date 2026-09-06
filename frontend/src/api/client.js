/**
 * api/client.js
 * Single responsibility: Thin wrapper around the backend API endpoints.
 * All network calls go through this file — components never fetch directly.
 *
 * Day 3: All functions call the real backend. mockResponses.js is quarantined
 * in src/api/__mocks__/ and is NOT imported here. If the backend is not ready,
 * a visible API error is surfaced in the UI (via simulationStore's errorMessage),
 * rather than silently falling back to mocks — which would blur live vs. precomputed.
 *
 * Endpoint reference: backend/app/api/routes.py
 * Request/response schemas: backend/app/api/schemas.py
 * Variable names: CONTROLS_SPEC.md §5
 */

const API_BASE =
  (typeof import.meta !== 'undefined' && import.meta.env?.VITE_API_BASE_URL) ||
  'http://localhost:8000';

// ─── Shared fetch helper ──────────────────────────────────────────────────────

/**
 * Thin fetch wrapper: throws a descriptive Error on non-2xx so callers
 * can catch and surface it in the UI rather than silently failing.
 * Never falls back to mock data — per Day 3 honesty constraint.
 */
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
 * @returns {Promise<SimulateResponse>}
 * @see CONTROLS_SPEC.md §5
 */
export async function simulate(params) {
  return apiFetch('/simulate', {
    method: 'POST',
    body: JSON.stringify(params),
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// GET /step
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Fetch a single generation step's cache state (for step-by-step animation).
 *
 * @param {string} sessionId
 * @param {number} stepIndex
 * @returns {Promise<StepResponse>}
 */
export async function getStep(sessionId, stepIndex) {
  return apiFetch(`/step/${sessionId}/${stepIndex}`);
}

// ─────────────────────────────────────────────────────────────────────────────
// GET /compare
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Fetch comparison data for all four policies at the same seq_len and budget.
 *
 * @param {{ budget: number, seq_len: number }} params
 * @returns {Promise<CompareResponse>}
 */
export async function compare(params) {
  const qs = new URLSearchParams(params).toString();
  return apiFetch(`/compare?${qs}`);
}

// ─────────────────────────────────────────────────────────────────────────────
// Precomputed data loaders — load JSON files, NOT the backend API
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Load the precomputed accuracy-vs-budget sweep curve.
 * Source: /data/precomputed/accuracy_vs_budget.json (served as a static asset).
 * Must be displayed with PrecomputedBadge (CONTROLS_SPEC §3 placement #1).
 *
 * @returns {Promise<Array<{budget: number, accuracy: number}>>}
 */
export async function loadAccuracyVsBudget() {
  return apiFetch('/data/precomputed/accuracy_vs_budget.json', { method: 'GET' });
}

/**
 * Load BDH published claims.
 * Source: /data/precomputed/bdh_published_claims.json (static asset).
 * Must be displayed with PrecomputedBadge (CONTROLS_SPEC §3 placement #2).
 *
 * @returns {Promise<object>}
 */
export async function loadBDHPublishedClaims() {
  return apiFetch('/data/precomputed/bdh_published_claims.json', { method: 'GET' });
}
