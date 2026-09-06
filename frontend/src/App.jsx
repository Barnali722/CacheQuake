/**
 * App.jsx
 * Single responsibility: Top-level layout shell — assembles all components into
 * the three-column "Memory Under Pressure" view and owns the walkthrough state.
 *
 * Day 2: Fully wired to SimulationProvider + real component implementations.
 * All data flows: ControlPanel → store → CacheHeatmap + MemoryChart + AccuracyPanel.
 */

import React, { useEffect } from 'react';
import { SimulationProvider, useSimulation } from './state/simulationStore';
import ControlPanel from './components/ControlPanel';
import CacheHeatmap from './components/CacheHeatmap';
import MemoryChart from './components/MemoryChart';
import AccuracyPanel from './components/AccuracyPanel';
import GuidedWalkthrough from './components/GuidedWalkthrough';
import BDHModule from './components/BDHModule';
import Sandbox from './components/Sandbox';

// ─── Styles ──────────────────────────────────────────────────────────────────
const appStyles = {
  shell: {
    display: 'grid',
    gridTemplateRows: 'auto auto 1fr',
    minHeight: '100vh',
    background: '#0f0f14',
    color: '#e0e0f0',
    fontFamily: "'Inter', system-ui, sans-serif",
    overflow: 'hidden',
  },
  topBar: {
    background: '#16161f',
    borderBottom: '1px solid #2a2a3a',
    padding: '10px 20px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: '12px',
  },
  topTitle: {
    fontSize: '15px',
    fontWeight: 700,
    color: '#e0e0f0',
    letterSpacing: '0.04em',
    whiteSpace: 'nowrap',
  },
  claimPill: {
    background: '#1e1e2e',
    border: '1px solid #333',
    padding: '4px 12px',
    borderRadius: '20px',
    fontSize: '10px',
    color: '#aaa',
    flex: 1,
    maxWidth: '680px',
    lineHeight: 1.4,
  },
  trackTag: {
    fontSize: '11px',
    color: '#555',
    whiteSpace: 'nowrap',
  },
  mainGrid: {
    display: 'grid',
    gridTemplateColumns: '260px 1fr 300px',
    overflow: 'hidden',
  },
  centerCol: {
    display: 'flex',
    flexDirection: 'column',
    borderLeft: '1px solid #2a2a3a',
    borderRight: '1px solid #2a2a3a',
    overflow: 'hidden',
  },
  heatmapPane: {
    flex: '0 0 auto',
    padding: '16px',
    borderBottom: '1px solid #2a2a3a',
    background: '#0f0f14',
    overflowY: 'auto',
    maxHeight: '320px',
  },
  chartPane: {
    flex: 1,
    padding: '16px',
    overflowY: 'auto',
  },
  rightCol: {
    display: 'flex',
    flexDirection: 'column',
    background: '#13131c',
    overflow: 'hidden',
  },
  rightTop: {
    flex: '0 0 auto',
    padding: '16px',
    borderBottom: '1px solid #2a2a3a',
    overflowY: 'auto',
    maxHeight: '55%',
  },
  rightBottom: {
    flex: 1,
    padding: '16px',
    overflowY: 'auto',
  },
  errorBar: {
    background: '#3a0000',
    border: '1px solid #ff6b6b',
    color: '#ff6b6b',
    padding: '6px 16px',
    fontSize: '12px',
  },
};

/** Inner app — must be inside SimulationProvider */
function AppInner() {
  const { state, dispatch, runSimulation } = useSimulation();
  const { controls, result, precomputed, ui } = state;

  // Run initial simulation on mount with defaults
  useEffect(() => {
    runSimulation();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const showBDH = controls.cachePolicy === 'bdh_recurrent' || ui.walkthroughStep === 4;

  return (
    <div id="app-shell" style={appStyles.shell}>

      {/* ── Top Bar ── */}
      <header style={appStyles.topBar}>
        <span style={appStyles.topTitle}>Memory Under Pressure</span>
        <div style={appStyles.claimPill}>
          "A Transformer's KV cache grows linearly because it stores an exact copy of the past.
          Eviction and compression cap that growth by trading exactness for a bounded budget.
          BDH removes the growth entirely with a fixed-size overwriting state."
        </div>
        <span style={appStyles.trackTag}>DataForge 2026 · Pathway × Rime</span>
      </header>

      {/* ── Error bar ── */}
      {ui.errorMessage && (
        <div style={appStyles.errorBar}>
          Error: {ui.errorMessage}
        </div>
      )}

      {/* ── Guided Walkthrough Banner ── */}
      {/* GuidedWalkthrough reads state directly via useSimulation — no props needed */}
      <GuidedWalkthrough />

      {/* ── Main 3-column grid ── */}
      <div style={appStyles.mainGrid}>

        {/* Left: ControlPanel */}
        <ControlPanel />

        {/* Center: Heatmap + Memory Chart */}
        <div style={appStyles.centerCol}>
          <div style={appStyles.heatmapPane}>
            <CacheHeatmap
              aliveTokenIndices={result.aliveTokenIndices}
              sequenceLength={controls.sequenceLength}
              needlePositions={result.needlePositions}
              cachePolicy={controls.cachePolicy}
              isLoading={ui.isLoading}
            />
          </div>
          <div style={appStyles.chartPane}>
            <MemoryChart
              cacheSizeHistory={result.cacheSizeHistory}
              baselineHistory={result.baselineHistory}
              cachePolicy={controls.cachePolicy}
              sequenceLength={controls.sequenceLength}
              isLoading={ui.isLoading}
            />
          </div>
        </div>

        {/* Right: AccuracyPanel + BDHModule (conditional) */}
        <div style={appStyles.rightCol}>
          <div style={appStyles.rightTop}>
            <AccuracyPanel
              modelAnswers={result.modelAnswers}
              correctAnswers={result.correctAnswers}
              liveAccuracyScore={result.accuracyScore}
              currentBudgetSize={controls.budgetSize}
              accuracyVsBudget={precomputed.accuracyVsBudget}
            />
          </div>
          {showBDH && (
            <div style={appStyles.rightBottom}>
              <BDHModule
                liveStats={{
                  cacheSizeTokens: result.cacheSizeTokens,
                  accuracyScore:   result.accuracyScore,
                }}
                publishedClaims={precomputed.bdhPublishedClaims}
              />
            </div>
          )}
        </div>

      </div>

      {/* Sandbox (shown when unlocked) */}
      {ui.sandboxUnlocked && <Sandbox isUnlocked={true} />}

    </div>
  );
}

/** App root — provides simulation context */
function App() {
  return (
    <SimulationProvider>
      <AppInner />
    </SimulationProvider>
  );
}

export default App;
