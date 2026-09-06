/**
 * state/simulationStore.js
 * Single responsibility: Hold and expose the current simulation state —
 * the four control values and the last simulation result — so all components
 * read from and write to one shared source of truth.
 *
 * Day 3: runSimulation() calls the real backend via api/client.js.
 * mockResponses.js is no longer imported here — it is quarantined in __mocks__/.
 * If the backend is unreachable, errorMessage is set and surfaced visibly in the UI.
 *
 * Variable names exactly match CONTROLS_SPEC.md §5 (Variable to API Mapping Summary).
 */

import React, { createContext, useContext, useReducer, useCallback } from 'react';
import { simulate, loadAccuracyVsBudget, loadBDHPublishedClaims } from '../api/client';

// ─────────────────────────────────────────────────────────────────────────────
// Initial state — variable names match CONTROLS_SPEC §5
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
  cacheSizeHistory:        [],
  baselineHistory:         [],
  needlePositions:         [],
};

export const DEFAULT_PRECOMPUTED = {
  accuracyVsBudget:   [],
  bdhPublishedClaims: null,
};

export const DEFAULT_UI = {
  walkthroughStep:  1,
  sandboxUnlocked:  false,
  isLoading:        false,
  errorMessage:     null,
  isMock:           false,  // Day 3: always false — real backend only
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

    case 'SET_CONTROLS_BATCH':
      // Used by GuidedWalkthrough to set multiple controls atomically
      return {
        ...state,
        controls: { ...state.controls, ...action.payload },
      };

    case 'SET_LOADING':
      return { ...state, ui: { ...state.ui, isLoading: action.payload, errorMessage: null } };

    case 'SET_RESULT': {
      const r = action.payload;
      return {
        ...state,
        result: {
          cacheSizeTokens:         r.cache_size_tokens          ?? null,
          fullCacheBaselineTokens: r.full_cache_baseline_tokens ?? null,
          aliveTokenIndices:       r.alive_token_indices        ?? [],
          modelAnswers:            r.model_answers              ?? [],
          correctAnswers:          r.ground_truth_answers       ?? [],
          accuracyScore:           r.accuracy_score             ?? null,
          cacheSizeHistory:        r.cache_size_history         ?? [],
          baselineHistory:         r.baseline_history           ?? [],
          needlePositions:         r.needle_positions           ?? [],
        },
        ui: { ...state.ui, isLoading: false, errorMessage: null, isMock: false },
      };
    }

    case 'SET_ERROR':
      return {
        ...state,
        ui: { ...state.ui, isLoading: false, errorMessage: action.payload },
      };

    case 'SET_PRECOMPUTED':
      return { ...state, precomputed: { ...state.precomputed, ...action.payload } };

    case 'ADVANCE_WALKTHROUGH':
      return {
        ...state,
        ui: { ...state.ui, walkthroughStep: Math.min(state.ui.walkthroughStep + 1, 5) },
      };

    case 'BACK_WALKTHROUGH':
      return {
        ...state,
        ui: { ...state.ui, walkthroughStep: Math.max(state.ui.walkthroughStep - 1, 1) },
      };

    case 'SET_WALKTHROUGH_STEP':
      return {
        ...state,
        ui: { ...state.ui, walkthroughStep: action.payload },
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
 */
export function SimulationProvider({ children }) {
  const [state, dispatch] = useReducer(reducer, INITIAL_STATE);

  /**
   * runSimulation — called by ControlPanel and GuidedWalkthrough on control change.
   * Calls the real backend via api/client.js simulate().
   * On error: sets errorMessage in UI state — never silently falls back to mock data.
   *
   * @param {object} overrides  Optional partial control overrides applied before the call.
   */
  const runSimulation = useCallback(async (overrides = {}) => {
    const controls = { ...state.controls, ...overrides };

    dispatch({ type: 'SET_LOADING', payload: true });
    try {
      // ── Real backend call ──────────────────────────────────────────────────
      const response = await simulate({
        policy:      controls.cachePolicy,
        budget:      controls.budgetSize,
        seq_len:     controls.sequenceLength,
        num_needles: controls.needleCount,
      });
      dispatch({ type: 'SET_RESULT', payload: response });

      // Load precomputed curve only if not already cached in the store.
      // Agent 3 response-time fix: the curve is a static file — no need to re-fetch
      // on every simulation. First load costs one HTTP request; subsequent runs are free.
      const alreadyCached =
        state.precomputed.accuracyVsBudget.length > 0 &&
        state.precomputed.bdhPublishedClaims !== null;

      if (!alreadyCached) {
        try {
          const curve = await loadAccuracyVsBudget();
          const bdh   = await loadBDHPublishedClaims();
          dispatch({
            type: 'SET_PRECOMPUTED',
            payload: { accuracyVsBudget: curve, bdhPublishedClaims: bdh },
          });
        } catch (precomputedErr) {
          // Precomputed data failing is not a blocking error — log, don't crash
          console.warn('Could not load precomputed data:', precomputedErr.message);
        }
      }
    } catch (err) {
      // Surface backend errors visibly — no silent mock fallback
      dispatch({ type: 'SET_ERROR', payload: err.message });
    }
  }, [state.controls, state.precomputed.accuracyVsBudget, state.precomputed.bdhPublishedClaims]);

  /**
   * applyWalkthroughStep — drives controls from GuidedWalkthrough steps.
   * Sets controls in the store AND runs a new simulation, so readouts update.
   *
   * @param {object} controlOverrides  e.g. { cachePolicy: 'sliding_window', budgetSize: 64 }
   */
  const applyWalkthroughStep = useCallback(async (controlOverrides) => {
    dispatch({ type: 'SET_CONTROLS_BATCH', payload: controlOverrides });
    await runSimulation(controlOverrides);
  }, [runSimulation]);

  return (
    <SimulationContext.Provider value={{ state, dispatch, runSimulation, applyWalkthroughStep }}>
      {children}
    </SimulationContext.Provider>
  );
}

/**
 * useSimulation — hook to access state and actions from any component.
 */
export function useSimulation() {
  const ctx = useContext(SimulationContext);
  if (!ctx) throw new Error('useSimulation must be used inside <SimulationProvider>');
  return ctx;
}

// Legacy export — kept for any import that hasn't been updated
export const simulationStore = null;
