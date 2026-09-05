/**
 * state/simulationStore.js
 * Single responsibility: Hold and expose the current simulation state —
 * the four control values and the last simulation result — so all components
 * read from and write to one shared source of truth.
 *
 * Variable names exactly match CONTROLS_SPEC.md §5 (Variable to API Mapping Summary).
 *
 * Implementation note: This is a plain JS module exporting an initial state shape.
 * Day 2 task: replace with Zustand store (or React context) — do not add logic here yet.
 *
 * @see CONTROLS_SPEC.md §5
 */

// ─────────────────────────────────────────────────────────────────────────────
// Control state (maps 1:1 to POST /simulate request fields)
// ─────────────────────────────────────────────────────────────────────────────

/**
 * @typedef {object} ControlState
 * @property {string} cachePolicy     - "full" | "sliding_window" | "heavy_hitter" | "bdh_recurrent"
 *                                      Maps to POST /simulate { policy }
 *                                      Default: "full" (CONTROLS_SPEC §1.1)
 * @property {number} budgetSize      - integer 8–512, step 8
 *                                      Maps to POST /simulate { budget }
 *                                      Default: 64 (CONTROLS_SPEC §1.2)
 * @property {number} sequenceLength  - integer 32–512, step 16
 *                                      Maps to POST /simulate { seq_len }
 *                                      Default: 128 (CONTROLS_SPEC §1.3)
 * @property {number} needleCount     - integer 1–5
 *                                      Maps to POST /simulate { num_needles }
 *                                      Default: 2 (CONTROLS_SPEC §1.4)
 */
export const DEFAULT_CONTROLS = {
  cachePolicy: 'full',
  budgetSize: 64,
  sequenceLength: 128,
  needleCount: 2,
};

// ─────────────────────────────────────────────────────────────────────────────
// Simulation result state (maps 1:1 to POST /simulate response fields)
// ─────────────────────────────────────────────────────────────────────────────

/**
 * @typedef {object} SimulationResult
 * @property {number|null}   cacheSizeTokens          - From /simulate { cache_size_tokens }        (Readout 2.1 live)
 * @property {number|null}   fullCacheBaselineTokens  - From /simulate { full_cache_baseline_tokens } (Readout 2.1 baseline)
 * @property {number[]}      aliveTokenIndices         - From /simulate { alive_token_indices }       (Readout 2.4 live)
 * @property {string[]}      modelAnswers              - From /simulate { model_answers }             (Readout 2.2 live)
 * @property {string[]}      correctAnswers            - From /simulate { ground_truth_answers }      (Readout 2.2 ground truth)
 * @property {number|null}   accuracyScore             - From /simulate { accuracy_score }            (Readout 2.3 live point)
 */
export const DEFAULT_SIMULATION_RESULT = {
  cacheSizeTokens: null,
  fullCacheBaselineTokens: null,
  aliveTokenIndices: [],
  modelAnswers: [],
  correctAnswers: [],
  accuracyScore: null,
};

// ─────────────────────────────────────────────────────────────────────────────
// Precomputed data state (loaded once at startup — NOT from live runs)
// ─────────────────────────────────────────────────────────────────────────────

/**
 * @typedef {object} PrecomputedData
 * @property {Array<{budget: number, accuracy: number}>} accuracyVsBudget
 *   From data/precomputed/accuracy_vs_budget.json — drives Readout 2.3 curve
 *   Must be shown with PrecomputedBadge (CONTROLS_SPEC §3 placement #1)
 *
 * @property {object|null} bdhPublishedClaims
 *   From data/precomputed/bdh_published_claims.json — drives BDHModule right column
 *   Must be shown with PrecomputedBadge (CONTROLS_SPEC §3 placement #2)
 */
export const DEFAULT_PRECOMPUTED = {
  accuracyVsBudget: [],
  bdhPublishedClaims: null,
};

// ─────────────────────────────────────────────────────────────────────────────
// UI / walkthrough state
// ─────────────────────────────────────────────────────────────────────────────

/**
 * @typedef {object} UIState
 * @property {number}  walkthroughStep    - Current guided step (1–5)
 * @property {boolean} sandboxUnlocked    - True after ComprehensionCheck passes
 * @property {boolean} isLoading          - True while /simulate request is in-flight
 * @property {string|null} errorMessage   - Last API error, or null
 */
export const DEFAULT_UI = {
  walkthroughStep: 1,
  sandboxUnlocked: false,
  isLoading: false,
  errorMessage: null,
};

// ─────────────────────────────────────────────────────────────────────────────
// Full initial state shape (merge of all above)
// Day 2: replace this export with a Zustand store create() call
// ─────────────────────────────────────────────────────────────────────────────

export const INITIAL_STATE = {
  controls: { ...DEFAULT_CONTROLS },
  result: { ...DEFAULT_SIMULATION_RESULT },
  precomputed: { ...DEFAULT_PRECOMPUTED },
  ui: { ...DEFAULT_UI },
};

// Placeholder for the store instance — will be a Zustand store on Day 2
export const simulationStore = null; // TODO Day 2: replace with create()(INITIAL_STATE)
