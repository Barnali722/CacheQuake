/**
 * App.jsx
 * Single responsibility: Top-level layout shell — assembles all components into
 * the "Memory Under Pressure" view and owns the walkthrough/sandbox flow.
 *
 * Day 4: Full experience: guided walkthrough → Sandbox → back to walkthrough.
 * Mobile-responsive layout via CSS class names added to DOM elements.
 */

import React, { useEffect, useState } from 'react';
import { SimulationProvider, useSimulation } from './state/simulationStore';
import ControlPanel from './components/ControlPanel';
import CacheHeatmap from './components/CacheHeatmap';
import MemoryChart from './components/MemoryChart';
import AccuracyPanel from './components/AccuracyPanel';
import GuidedWalkthrough from './components/GuidedWalkthrough';
import BDHModule from './components/BDHModule';
import Sandbox from './components/Sandbox';
import '../styles/index.css';

// ─── Styles (desktop — mobile overrides live in index.css) ───────────────────
const appStyles = {
  shell: {
    display: 'flex',
    flexDirection: 'column',
    minHeight: '100vh',
    background: '#0f0f14',
    color: '#e0e0f0',
    fontFamily: "'Inter', system-ui, sans-serif",
    overflowX: 'hidden',
  },
  topBar: {
    background: '#16161f',
    borderBottom: '1px solid #2a2a3a',
    padding: '10px 20px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: '12px',
    flexShrink: 0,
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
    flex: 1,
    overflow: 'hidden',
    minHeight: 0,
  },
  centerCol: {
    display: 'flex',
    flexDirection: 'column',
    borderLeft: '1px solid #2a2a3a',
    borderRight: '1px solid #2a2a3a',
    overflow: 'hidden',
    minHeight: 0,
  },
  heatmapPane: {
    flex: '0 0 auto',
    padding: '16px',
    borderBottom: '1px solid #2a2a3a',
    background: '#0f0f14',
    overflowY: 'auto',
    maxHeight: '340px',
  },
  chartPane: {
    flex: 1,
    padding: '16px',
    overflowY: 'auto',
    minHeight: 0,
  },
  rightCol: {
    display: 'flex',
    flexDirection: 'column',
    background: '#13131c',
    overflow: 'hidden',
    minHeight: 0,
  },
  rightTop: {
    flex: '1 1 auto',
    padding: '16px',
    borderBottom: '1px solid #2a2a3a',
    overflowY: 'auto',
    minHeight: 0,
  },
  rightBottom: {
    flex: '1 1 auto',
    padding: '16px',
    overflowY: 'auto',
    minHeight: 0,
  },
  errorBar: {
    background: '#3a0000',
    borderBottom: '1px solid #ff6b6b',
    color: '#ff6b6b',
    padding: '6px 16px',
    fontSize: '12px',
    flexShrink: 0,
  },
  // Mode toggle bar (guided ↔ sandbox)
  modeToggleBar: {
    background: '#13131c',
    borderBottom: '1px solid #2a2a44',
    padding: '6px 16px',
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
    flexShrink: 0,
  },
  modeBtn: (active) => ({
    fontSize: '11px',
    fontWeight: active ? 600 : 400,
    background: active ? 'rgba(123,140,255,0.12)' : 'transparent',
    border: `1px solid ${active ? '#7b8cff' : '#333'}`,
    color: active ? '#7b8cff' : '#666',
    padding: '4px 14px',
    borderRadius: '4px',
    cursor: 'pointer',
    fontFamily: 'inherit',
    minHeight: '32px',
  }),
};

/** Inner app — must be inside SimulationProvider */
function AppInner() {
  const { state, dispatch, runSimulation } = useSimulation();
  const { controls, result, precomputed, ui } = state;

  // Local mode: 'guided' | 'sandbox'
  const [mode, setMode] = useState('guided');

  // Run initial simulation on mount
  useEffect(() => {
    runSimulation();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Auto-open sandbox when unlocked via walkthrough completion
  useEffect(() => {
    if (ui.sandboxUnlocked && mode === 'guided') {
      setMode('sandbox');
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ui.sandboxUnlocked]);

  const showBDH = controls.cachePolicy === 'bdh_recurrent' || ui.walkthroughStep === 4;

  const handleReturnToWalkthrough = () => {
    setMode('guided');
    dispatch({ type: 'SET_WALKTHROUGH_STEP', payload: 5 });
  };

  const handleEnterSandbox = () => {
    dispatch({ type: 'UNLOCK_SANDBOX' });
    setMode('sandbox');
  };

  return (
    <div id="app-shell" style={appStyles.shell}>

      {/* ── Top Bar ── */}
      <header style={appStyles.topBar}>
        <span style={appStyles.topTitle}>Memory Under Pressure</span>
        <div className="topbar-claim-pill" style={appStyles.claimPill}>
          "A Transformer's KV cache grows linearly — it stores an exact copy of the past.
          Eviction and compression cap that growth by trading exactness for a bounded budget.
          BDH removes the growth entirely with a fixed-size overwriting state."
        </div>
        <span className="topbar-track-tag" style={appStyles.trackTag}>
          DataForge 2026 · Pathway × Rime
        </span>
      </header>

      {/* ── Error bar ── */}
      {ui.errorMessage && (
        <div style={appStyles.errorBar} role="alert">
          ⚠ {ui.errorMessage}
        </div>
      )}

      {/* ── Mode toggle bar ── */}
      <div style={appStyles.modeToggleBar}>
        <button
          style={appStyles.modeBtn(mode === 'guided')}
          onClick={() => setMode('guided')}
          aria-pressed={mode === 'guided'}
          aria-label="Switch to guided walkthrough"
        >
          📖 Guided Walkthrough
        </button>
        <button
          style={appStyles.modeBtn(mode === 'sandbox')}
          onClick={handleEnterSandbox}
          aria-pressed={mode === 'sandbox'}
          aria-label="Switch to sandbox free-play"
        >
          🧪 Sandbox
          {ui.sandboxUnlocked && (
            <span style={{ marginLeft: '6px', fontSize: '9px',
              color: '#3dffa0', background: 'rgba(61,255,160,0.1)',
              padding: '1px 5px', borderRadius: '2px', border: '1px solid #3dffa0' }}>
              UNLOCKED
            </span>
          )}
        </button>
        <span style={{ fontSize: '10px', color: '#444', marginLeft: '4px' }}>
          {mode === 'guided'
            ? `Step ${ui.walkthroughStep} of 5`
            : 'Free play — all controls unlocked'}
        </span>
      </div>

      {/* ── GUIDED MODE ── */}
      {mode === 'guided' && (
        <>
          {/* Walkthrough banner */}
          <GuidedWalkthrough />

          {/* Main 3-column grid */}
          <div className="main-grid" style={appStyles.mainGrid}>

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

            {/* Right: AccuracyPanel + BDHModule */}
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
        </>
      )}

      {/* ── SANDBOX MODE ── */}
      {mode === 'sandbox' && (
        <Sandbox
          isUnlocked={ui.sandboxUnlocked}
          onReturnToWalkthrough={handleReturnToWalkthrough}
        />
      )}

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
