/**
 * api/client.js
 * Single responsibility: Thin wrapper around the backend API endpoints.
 * All network calls go through this file — components never fetch directly.
 *
 * Backend base URL is read from the environment variable VITE_API_BASE_URL.
 * All functions are stubs that throw "not implemented" until Day 2.
 *
 * Endpoint reference: backend/app/api/routes.py
 * Request/response schemas: backend/app/api/schemas.py
 * Variable names: CONTROLS_SPEC.md §5 (Variable to API Mapping Summary)
 */

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// ─────────────────────────────────────────────────────────────────────────────
// POST /simulate
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Run a full simulation with the given parameters.
 *
 * @param {object} params
 * @param {string} params.policy         - cachePolicy: "full" | "sliding_window" | "heavy_hitter" | "bdh_recurrent"
 * @param {number} params.budget         - budgetSize: integer 8–512
 * @param {number} params.seq_len        - sequenceLength: integer 32–512
 * @param {number} params.num_needles    - needleCount: integer 1–5
 *
 * @returns {Promise<SimulateResponse>}
 * @typedef {object} SimulateResponse
 * @property {number}   cache_size_tokens           - Live: tokens currently in cache (Readout 2.1)
 * @property {number}   full_cache_baseline_tokens  - Baseline: full-cache token count (Readout 2.1)
 * @property {number[]} alive_token_indices          - Live: which token positions are in cache (Readout 2.4)
 * @property {string[]} model_answers                - Live: model's answers to needle questions (Readout 2.2)
 * @property {string[]} ground_truth_answers         - Live: correct answers from task generator (Readout 2.2)
 * @property {number}   accuracy_score               - Live: fraction correct (0–1), for Readout 2.3 live point
 *
 * @see CONTROLS_SPEC.md §5
 */
export async function simulate(params) {
  throw new Error('simulate() — not implemented. Day 2 task: wire POST /simulate.');
}

// ─────────────────────────────────────────────────────────────────────────────
// GET /step (optional per-step streaming)
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Fetch a single generation step's cache state (for live step-by-step animation).
 *
 * @param {string} sessionId  - Session ID returned by /simulate
 * @param {number} stepIndex  - Generation step index (0-based)
 *
 * @returns {Promise<StepResponse>}
 * @typedef {object} StepResponse
 * @property {number}   cache_size_tokens   - Tokens in cache at this step
 * @property {number[]} alive_token_indices - Which tokens are alive at this step
 */
export async function getStep(sessionId, stepIndex) {
  throw new Error('getStep() — not implemented. Day 2 task: wire GET /step.');
}

// ─────────────────────────────────────────────────────────────────────────────
// GET /compare (policy comparison endpoint)
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Fetch comparison data for all four policies at the same seq_len and budget.
 * Used for the trade-off table shown in walkthrough step 5.
 *
 * @param {object} params
 * @param {number} params.budget    - budgetSize
 * @param {number} params.seq_len   - sequenceLength
 *
 * @returns {Promise<CompareResponse>}
 * @typedef {object} CompareResponse
 * @property {object} full          - Stats for "full" policy
 * @property {object} sliding_window - Stats for "sliding_window" policy
 * @property {object} heavy_hitter  - Stats for "heavy_hitter" policy
 * @property {object} bdh_recurrent - Stats for "bdh_recurrent" policy
 */
export async function compare(params) {
  throw new Error('compare() — not implemented. Day 3 task: wire GET /compare.');
}

// ─────────────────────────────────────────────────────────────────────────────
// Precomputed data loaders (NOT live API calls — load from data/precomputed/)
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Load the precomputed accuracy-vs-budget sweep curve.
 * Data source: data/precomputed/accuracy_vs_budget.json
 * This data is NOT from a live run — must be displayed with PrecomputedBadge.
 *
 * @returns {Promise<Array<{budget: number, accuracy: number}>>}
 * @see CONTROLS_SPEC.md §2.3
 */
export async function loadAccuracyVsBudget() {
  throw new Error('loadAccuracyVsBudget() — not implemented. Day 2 task: fetch accuracy_vs_budget.json.');
}

/**
 * Load BDH published claims from precomputed data.
 * Data source: data/precomputed/bdh_published_claims.json
 * Sourced from arXiv:2509.26507 — NOT reproduced by our team.
 * Must be displayed with PrecomputedBadge.
 *
 * @returns {Promise<object>}
 * @see CONTROLS_SPEC.md §2.5
 */
export async function loadBDHPublishedClaims() {
  throw new Error('loadBDHPublishedClaims() — not implemented. Day 3 task: fetch bdh_published_claims.json.');
}
