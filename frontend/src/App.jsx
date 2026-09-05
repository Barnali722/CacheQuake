/**
 * App.jsx
 * Single responsibility: Top-level layout shell — assembles all components into
 * the three-column "Memory Under Pressure" view and owns the walkthrough state.
 */

import React from 'react';
import ControlPanel from './components/ControlPanel';
import CacheHeatmap from './components/CacheHeatmap';
import MemoryChart from './components/MemoryChart';
import AccuracyPanel from './components/AccuracyPanel';
import GuidedWalkthrough from './components/GuidedWalkthrough';
import ComprehensionCheck from './components/ComprehensionCheck';
import BDHModule from './components/BDHModule';
import Sandbox from './components/Sandbox';
import { INITIAL_STATE } from './state/simulationStore';

/**
 * App
 *
 * Renders the full "Memory Under Pressure" layout:
 *   - Top bar (title + claim)
 *   - GuidedWalkthrough banner
 *   - Three-column grid: ControlPanel | CacheHeatmap+MemoryChart | AccuracyPanel+BDHModule
 *
 * State management will be wired to simulationStore on Day 2.
 * All component props are currently passed as defaults from INITIAL_STATE.
 */
function App() {
  return (
    <div id="app-shell">
      {/* ── Not yet implemented placeholder ── */}
      <div>App — not yet implemented</div>

      {/*
        Day 2 implementation notes:
        - Wire INITIAL_STATE from simulationStore to all component props.
        - Top bar: render title "Memory Under Pressure" + one-sentence claim pill.
        - GuidedWalkthrough: currentStep from ui.walkthroughStep.
        - ControlPanel: all four controls from state.controls.
        - CacheHeatmap: aliveTokenIndices from state.result.aliveTokenIndices.
        - MemoryChart: memoryUsedHistory and memoryBaselineHistory from result.
        - AccuracyPanel: modelAnswers, correctAnswers, liveAccuracyScore, accuracyVsBudget.
        - BDHModule: liveStats when cachePolicy === "bdh_recurrent"; publishedClaims always.
        - ComprehensionCheck: shown between step 4 and step 5.
        - Sandbox: shown when ui.sandboxUnlocked === true.
      */}
    </div>
  );
}

export default App;
