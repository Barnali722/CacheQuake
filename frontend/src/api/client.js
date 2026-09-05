/**
 * api/client.js
 * Single responsibility: Thin wrapper around the backend API endpoints.
 * All network calls go through this file — components never fetch directly.
 *
 * Day 2: simulate() and loadAccuracyVsBudget() are backed by mockResponses.js.
 *        The exported function signatures are IDENTICAL to what the real backend requires.
 *        Day 3 swap: remove the mock import lines and uncomment the fetch() blocks.
 *
 * Endpoint reference: backend/app/api/routes.py
 * Request/response schemas: backend/app/api/schemas.py
 * Variable names: CONTROLS_SPEC.md §5
 */

// ── Day 2 mock imports — REMOVE these on Day 3 ──────────────────────────────
import {
  getMockResponse,
  getMockAccuracyVsBudgetCurve,
  MOCK_BDH_PUBLISHED_CLAIMS,
} from './mockResponses';
// ── End Day 2 mock imports ───────────────────────────────────────────────────

const API_BASE = (typeof import.meta !== 'undefined' && import.meta.env?.VITE_API_BASE_URL)
  || 'http://localhost:8000';

// ─────────────────────────────────────────────────────────────────────────────
// POST /simulate
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Run a full simulation with the given parameters.
 *
 * @param {object} params
 * @param {string} params.policy         - cachePolicy: "full"|"sliding_window"|"heavy_hitter"|"bdh_recurrent"
 * @param {number} params.budget         - budgetSize: integer 8–512
 * @param {number} params.seq_len        - sequenceLength: integer 32–512
 * @param {number} params.num_needles    - needleCount: integer 1–5
 *
 * @returns {Promise<SimulateResponse>}
 * @see CONTROLS_SPEC.md §5
 */
export async function simulate(params) {
  // ── Day 2 MOCK — replace this block on Day 3 ────────────────────────────
  return getMockResponse(params);
  // ── Day 3 REAL — uncomment this block when backend is ready ─────────────
  // const res = await fetch(`${API_BASE}/simulate`, {
  //   method: 'POST',
  //   headers: { 'Content-Type': 'application/json' },
  //   body: JSON.stringify(params),
  // });
  // if (!res.ok) throw new Error(`/simulate failed: ${res.status} ${res.statusText}`);
  // return res.json();
  // ── End Day 3 block ───────────────────────────────────────────────────────
}

// ─────────────────────────────────────────────────────────────────────────────
// GET /step
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Fetch a single generation step's cache state.
 * @param {string} sessionId
 * @param {number} stepIndex
 * @returns {Promise<StepResponse>}
 */
export async function getStep(sessionId, stepIndex) {
  // Day 3 implementation:
  // const res = await fetch(`${API_BASE}/step/${sessionId}/${stepIndex}`);
  // if (!res.ok) throw new Error(`/step failed: ${res.status}`);
  // return res.json();
  throw new Error('getStep() — not implemented until Day 3 (live backend).');
}

// ─────────────────────────────────────────────────────────────────────────────
// GET /compare
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Fetch comparison data for all four policies.
 * @param {{ budget: number, seq_len: number }} params
 * @returns {Promise<CompareResponse>}
 */
export async function compare(params) {
  // Day 3 implementation:
  // const res = await fetch(`${API_BASE}/compare?${new URLSearchParams(params)}`);
  // if (!res.ok) throw new Error(`/compare failed: ${res.status}`);
  // return res.json();
  throw new Error('compare() — not implemented until Day 3 (live backend).');
}

// ─────────────────────────────────────────────────────────────────────────────
// Precomputed data loaders
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Load the precomputed accuracy-vs-budget sweep curve.
 * Must be displayed with PrecomputedBadge (CONTROLS_SPEC §3 placement #1).
 *
 * @param {string} policy
 * @param {number} seq_len
 * @param {number} num_needles
 * @returns {Promise<Array<{budget: number, accuracy: number}>>}
 */
export async function loadAccuracyVsBudget(policy, seq_len, num_needles) {
  // ── Day 2 MOCK — replace on Day 3 ───────────────────────────────────────
  return getMockAccuracyVsBudgetCurve(policy, seq_len, num_needles);
  // ── Day 3 REAL ────────────────────────────────────────────────────────────
  // const res = await fetch('/data/precomputed/accuracy_vs_budget.json');
  // return res.json();
}

/**
 * Load BDH published claims.
 * Must be displayed with PrecomputedBadge (CONTROLS_SPEC §3 placement #2).
 *
 * @returns {Promise<object>}
 */
export async function loadBDHPublishedClaims() {
  // ── Day 2 MOCK — replace on Day 3 ───────────────────────────────────────
  return MOCK_BDH_PUBLISHED_CLAIMS;
  // ── Day 3 REAL ────────────────────────────────────────────────────────────
  // const res = await fetch('/data/precomputed/bdh_published_claims.json');
  // return res.json();
}
