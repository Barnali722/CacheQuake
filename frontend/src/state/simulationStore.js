/**
 * state/simulationStore.js
 * Single responsibility: Hold and expose the current simulation state —
 * the four control values and the last simulation result — so all components
 * read from and write to one shared source of truth.
 *
 * Day 2: Implemented as React Context + useReducer (no external library).
 * Day 3: Swap dispatch({ type: 'SET_RESULT', payload: response }) callers to
 *         use the real API; zero changes needed in this file or in components.
 *
 * Variable names exactly match CONTROLS_SPEC.md §5 (Variable to API Mapping Summary).
 */

import React, { createContext, useContext, useReducer, useCallback } from 'react';
import { getMockResponse, getMockAccuracyVsBudgetCurve, MOCK_BDH_PUBLISHED_CLAIMS } from '../api/mockResponses';

// ─────────────────────────────────────────────────────────────────────────────
// Initial state shape — variable names match CONTROLS_SPEC §5
// ─────────────────────────────────────────────────────────────────────────────

export const DEFAULT_CONTROLS = {
  cachePolicy:    'full',   // CONTROLS_SPEC §1.1
  budgetSize:     64,       // CONTROLS_SPEC §1.2
  sequenceLength: 128,      // CONTROLS_SPEC §1.3
  needleCount:    2,        // CONTROLS_SPEC §1.4
};

export const DEFAULT_SIMULATION_RESULT = {
  cacheSizeTokens:         null,
  fullCacheBaselineTokens: null,
  aliveTokenIndices:       [],
  modelAnswers:            [],
  correctAnswers:          [],
  accuracyScore:           null,
  // Extended fields for chart history (per-step arrays)
  cacheSizeHistory:        [],
  baselineHistory:         [],
  needlePositions:         [],
};

export const DEFAULT_PRECOMPUTED = {
  accuracyVsBudget:   [],
  bdhPublishedClaims: null,
};

export const DEFAULT_UI = {
  walkthroughStep: 1,
  sandboxUnlocked: false,
  isLoading:       false,
  errorMessage:    null,
  isMock:          true,   // Day 3: set false when wired to real backend
};

export const INITIAL_STATE = {
  controls:    { ...DEFAULT_CONTROLS },
  result:      { ...DEFAULT_SIMULATION_RESULT },
  precomputed: { ...DEFAULT_PRECOMPUTED },
  ui:          { ...DEFAULT_UI },
};

// ─────────────────────────────────────────────────────────────────────────────
// Reducer
// ─────────────────────────────────────────────────────────────────────────────

function reducer(state, action) {
  switch (action.type) {

    case 'SET_CONTROL': {
      const { field, value } = action.payload;
      return {
        ...state,
        controls: { ...state.controls, [field]: value },
      };
    }

    case 'SET_LOADING':
      return { ...state, ui: { ...state.ui, isLoading: action.payload, errorMessage: null } };

    case 'SET_RESULT': {
      const r = action.payload; // raw API response fields (snake_case from API)
      return {
        ...state,
        result: {
          cacheSizeTokens:         r.cache_size_tokens,
          fullCacheBaselineTokens: r.full_cache_baseline_tokens,
          aliveTokenIndices:       r.alive_token_indices       ?? [],
          modelAnswers:            r.model_answers             ?? [],
          correctAnswers:          r.ground_truth_answers      ?? [],
          accuracyScore:           r.accuracy_score            ?? null,
          cacheSizeHistory:        r.cache_size_history        ?? [],
          baselineHistory:         r.baseline_history          ?? [],
          needlePositions:         r.needle_positions          ?? [],
        },
        ui: { ...state.ui, isLoading: false, errorMessage: null, isMock: r.__mock === true },
      };
    }

    case 'SET_ERROR':
      return { ...state, ui: { ...state.ui, isLoading: false, errorMessage: action.payload } };

    case 'SET_PRECOMPUTED':
      return { ...state, precomputed: { ...state.precomputed, ...action.payload } };

    case 'ADVANCE_WALKTHROUGH':
      return {
        ...state,
        ui: {
          ...state.ui,
          walkthroughStep: Math.min(state.ui.walkthroughStep + 1, 5),
        },
      };

    case 'BACK_WALKTHROUGH':
      return {
        ...state,
        ui: {
          ...state.ui,
          walkthroughStep: Math.max(state.ui.walkthroughStep - 1, 1),
        },
      };

    case 'UNLOCK_SANDBOX':
      return { ...state, ui: { ...state.ui, sandboxUnlocked: true } };

    default:
      return state;
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Context
// ─────────────────────────────────────────────────────────────────────────────

const SimulationContext = createContext(null);

/**
 * SimulationProvider — wrap the app root with this.
 * Provides state and dispatch to all child components.
 */
export function SimulationProvider({ children }) {
  const [state, dispatch] = useReducer(reducer, INITIAL_STATE);

  /**
   * runSimulation — called by ControlPanel on any control change.
   * Day 2: calls getMockResponse (mock-backed).
   * Day 3: swap getMockResponse for the real simulate() from api/client.js.
   *
   * @param {object} overrides  Optional partial control overrides (applied before the call)
   */
  const runSimulation = useCallback(async (overrides = {}) => {
    // Merge current controls with any overrides from the control that just changed
    const controls = { ...state.controls, ...overrides };

    dispatch({ type: 'SET_LOADING', payload: true });
    try {
      // ── Day 2: MOCK ─────────────────────────────────────────────────────
      // Replace this block on Day 3 with:
      //   import { simulate } from '../api/client';
      //   const response = await simulate({ policy: controls.cachePolicy, budget: controls.budgetSize, ... });
      const response = await new Promise((resolve) =>
        setTimeout(
          () =>
            resolve(
              getMockResponse({
                policy:      controls.cachePolicy,
                budget:      controls.budgetSize,
                seq_len:     controls.sequenceLength,
                num_needles: controls.needleCount,
              })
            ),
          120 // simulate ~120ms network latency
        )
      );
      // ── End mock block ───────────────────────────────────────────────────

      dispatch({ type: 'SET_RESULT', payload: response });

      // Also refresh the precomputed accuracy-vs-budget curve for the new policy
      // Day 3: replace getMockAccuracyVsBudgetCurve with loadAccuracyVsBudget() fetch
      const curve = getMockAccuracyVsBudgetCurve(
        controls.cachePolicy,
        controls.sequenceLength,
        controls.needleCount
      );
      dispatch({
        type: 'SET_PRECOMPUTED',
        payload: {
          accuracyVsBudget:   curve,
          bdhPublishedClaims: MOCK_BDH_PUBLISHED_CLAIMS,
        },
      });
    } catch (err) {
      dispatch({ type: 'SET_ERROR', payload: err.message });
    }
  }, [state.controls]);

  return (
    <SimulationContext.Provider value={{ state, dispatch, runSimulation }}>
      {children}
    </SimulationContext.Provider>
  );
}

/**
 * useSimulation — hook to access state and actions from any component.
 * Returns { state, dispatch, runSimulation }.
 */
export function useSimulation() {
  const ctx = useContext(SimulationContext);
  if (!ctx) throw new Error('useSimulation must be used inside <SimulationProvider>');
  return ctx;
}

// Keep legacy export for backwards compatibility with Day 1 imports
export const simulationStore = null; // replaced by SimulationProvider + useSimulation
