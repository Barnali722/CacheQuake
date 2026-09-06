/**
 * state/simulationStore.jsx   ← renamed from .js (contained JSX)
 *
 * Single responsibility: Hold and expose the current simulation state.
 * Variable names exactly match CONTROLS_SPEC.md §5.
 *
 * DEMO MODE: When the backend at localhost:8000 is unreachable, the store
 * falls back to deterministic mock data so the UI is fully demoable without
 * a running backend. The mock fallback is clearly labelled with isMock=true
 * in ui state — components surface a "DEMO MODE" badge (not PrecomputedBadge).
 */

import React, { createContext, useContext, useReducer, useCallback } from 'react';
import { simulate, loadAccuracyVsBudget, loadBDHPublishedClaims } from '../api/client';

// ─────────────────────────────────────────────────────────────────────────────
// Initial state
// ─────────────────────────────────────────────────────────────────────────────
export const DEFAULT_CONTROLS = {
  cachePolicy:    'full',
  budgetSize:     64,
  sequenceLength: 128,
  needleCount:    2,
};

const EMPTY_RESULT = {
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

export const INITIAL_STATE = {
  controls:    { ...DEFAULT_CONTROLS },
  result:      { ...EMPTY_RESULT },
  precomputed: { accuracyVsBudget: [], bdhPublishedClaims: null },
  ui: {
    walkthroughStep: 1,
    sandboxUnlocked: false,
    isLoading:       false,
    errorMessage:    null,
    isMock:          false,
  },
};

// ─────────────────────────────────────────────────────────────────────────────
// Mock data generator (demo fallback when backend is unreachable)
// ─────────────────────────────────────────────────────────────────────────────
function buildMockResult(controls) {
  const { cachePolicy, budgetSize, sequenceLength, needleCount } = controls;
  const seqLen = sequenceLength;

  // Full-cache baseline always grows linearly
  const baselineHistory = Array.from({ length: seqLen }, (_, i) => i + 1);

  let aliveTokenIndices = [];
  let cacheSizeHistory  = [];

  if (cachePolicy === 'full') {
    aliveTokenIndices = Array.from({ length: seqLen }, (_, i) => i);
    cacheSizeHistory  = baselineHistory.slice();
  } else if (cachePolicy === 'sliding_window') {
    const start = Math.max(0, seqLen - budgetSize);
    aliveTokenIndices = Array.from({ length: seqLen - start }, (_, i) => start + i);
    cacheSizeHistory  = Array.from({ length: seqLen }, (_, i) => Math.min(i + 1, budgetSize));
  } else if (cachePolicy === 'heavy_hitter') {
    // Scatter alive tokens — high-attention tokens survive
    const stride = Math.max(1, Math.floor(seqLen / budgetSize));
    aliveTokenIndices = Array.from({ length: Math.min(budgetSize, seqLen) }, (_, i) => i * stride);
    cacheSizeHistory  = Array.from({ length: seqLen }, (_, i) => Math.min(i + 1, budgetSize));
  } else if (cachePolicy === 'bdh_recurrent') {
    // Fixed-size — flat memory, spread tokens
    const count = Math.min(budgetSize, seqLen);
    const stride = Math.max(1, Math.floor(seqLen / count));
    aliveTokenIndices = Array.from({ length: count }, (_, i) => i * stride);
    cacheSizeHistory  = Array.from({ length: seqLen }, () => budgetSize);
  }

  // Needle positions: evenly spread through sequence
  const needlePositions = Array.from(
    { length: needleCount },
    (_, i) => Math.floor((i + 1) * seqLen / (needleCount + 1))
  );

  // Accuracy: needles in alive set = retrieved
  const aliveSet = new Set(aliveTokenIndices);
  const retrieved = needlePositions.filter(p => aliveSet.has(p)).length;
  const accuracyScore = needlePositions.length > 0 ? retrieved / needlePositions.length : 1;

  const answers = ['Paris', 'Newton', 'DNA', 'Einstein', 'Curie'];
  const modelAnswers   = needlePositions.map((p, i) =>
    aliveSet.has(p) ? answers[i % answers.length] : '?'
  );
  const correctAnswers = needlePositions.map((_, i) => answers[i % answers.length]);

  return {
    cache_size_tokens:          aliveTokenIndices.length,
    full_cache_baseline_tokens: seqLen,
    alive_token_indices:        aliveTokenIndices,
    model_answers:              modelAnswers,
    ground_truth_answers:       correctAnswers,
    accuracy_score:             accuracyScore,
    cache_size_history:         cacheSizeHistory,
    baseline_history:           baselineHistory,
    needle_positions:           needlePositions,
  };
}

// Mock precomputed accuracy-vs-budget curve
function buildMockCurve() {
  return Array.from({ length: 32 }, (_, i) => ({
    budget:   (i + 1) * 16,
    accuracy: Math.min(0.98, 0.3 + 0.022 * (i + 1)),
  }));
}

// ─────────────────────────────────────────────────────────────────────────────
// Reducer
// ─────────────────────────────────────────────────────────────────────────────
function reducer(state, action) {
  switch (action.type) {
    case 'SET_CONTROL':
      return { ...state, controls: { ...state.controls, [action.payload.field]: action.payload.value } };
    case 'SET_CONTROLS_BATCH':
      return { ...state, controls: { ...state.controls, ...action.payload } };
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
        ui: { ...state.ui, isLoading: false, errorMessage: null, isMock: action.isMock ?? false },
      };
    }
    case 'SET_ERROR':
      return { ...state, ui: { ...state.ui, isLoading: false, errorMessage: action.payload } };
    case 'SET_PRECOMPUTED':
      return { ...state, precomputed: { ...state.precomputed, ...action.payload } };
    case 'ADVANCE_WALKTHROUGH':
      return { ...state, ui: { ...state.ui, walkthroughStep: Math.min(state.ui.walkthroughStep + 1, 5) } };
    case 'BACK_WALKTHROUGH':
      return { ...state, ui: { ...state.ui, walkthroughStep: Math.max(state.ui.walkthroughStep - 1, 1) } };
    case 'SET_WALKTHROUGH_STEP':
      return { ...state, ui: { ...state.ui, walkthroughStep: action.payload } };
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

export function SimulationProvider({ children }) {
  const [state, dispatch] = useReducer(reducer, INITIAL_STATE);

  const runSimulation = useCallback(async (overrides = {}) => {
    const controls = { ...state.controls, ...overrides };
    dispatch({ type: 'SET_LOADING', payload: true });
    try {
      // ── Try real backend first ──────────────────────────────────────────
      const response = await simulate({
        policy:      controls.cachePolicy,
        budget:      controls.budgetSize,
        seq_len:     controls.sequenceLength,
        num_needles: controls.needleCount,
      });
      dispatch({ type: 'SET_RESULT', payload: response, isMock: false });

      // Load precomputed curve (once only)
      if (state.precomputed.accuracyVsBudget.length === 0) {
        try {
          const curve = await loadAccuracyVsBudget();
          const bdh   = await loadBDHPublishedClaims();
          dispatch({ type: 'SET_PRECOMPUTED', payload: { accuracyVsBudget: curve, bdhPublishedClaims: bdh } });
        } catch (_) { /* precomputed optional */ }
      }
    } catch (_backendErr) {
      // ── Backend unreachable → use mock data for demo ────────────────────
      const mockResult = buildMockResult(controls);
      dispatch({ type: 'SET_RESULT', payload: mockResult, isMock: true });

      if (state.precomputed.accuracyVsBudget.length === 0) {
        dispatch({ type: 'SET_PRECOMPUTED', payload: {
          accuracyVsBudget:   buildMockCurve(),
          bdhPublishedClaims: { claims: [
            { label: 'Memory growth', value: 'O(1) — constant' },
            { label: 'Benchmark accuracy', value: '~89% (arXiv)' },
          ]},
        }});
      }
    }
  }, [state.controls, state.precomputed.accuracyVsBudget.length]);

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

export function useSimulation() {
  const ctx = useContext(SimulationContext);
  if (!ctx) throw new Error('useSimulation must be used inside <SimulationProvider>');
  return ctx;
}
