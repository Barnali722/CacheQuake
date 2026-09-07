/**
 * Sandbox.jsx
 * Single responsibility: Render the free-play mode view where all four controls
 * (cachePolicy, budgetSize, sequenceLength, needleCount) are unlocked simultaneously,
 * without guided walkthrough constraints, per PRD §4.3.
 *
 * Day 4: Fully implemented. Uses the SAME simulationStore + api/client.js as the
 * guided flow — Sandbox is NOT a separate code path. It is the same live wiring
 * with the walkthrough's narrative rails removed.
 */

import React from 'react';
import { useSimulation } from '../state/simulationStore';
import CacheHeatmap from './CacheHeatmap';
import MemoryChart from './MemoryChart';
import AccuracyPanel from './AccuracyPanel';
import BDHModule from './BDHModule';

// ─── Styles ──────────────────────────────────────────────────────────────────
const s = {
  // Locked overlay
  lockedWrapper: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '32px 20px',
    background: '#0f0f14',
    borderTop: '1px solid #2a2a3a',
    gap: '12px',
    textAlign: 'center',
  },
  lockIcon: { fontSize: '28px' },
  lockTitle: { fontSize: '14px', color: '#e0e0f0', fontWeight: 600 },
  lockDesc: { fontSize: '12px', color: '#888', maxWidth: '360px', lineHeight: 1.6 },

  // Unlocked sandbox
  sandboxWrapper: {
    background: '#0f0f14',
    borderTop: '2px solid #7b8cff',
  },
  sandboxHeader: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    padding: '10px 20px',
    background: '#16161f',
    borderBottom: '1px solid #2a2a44',
    flexWrap: 'wrap',
  },
  sandboxTitle: {
    fontSize: '13px',
    fontWeight: 700,
    color: '#c0c8ff',
    letterSpacing: '0.04em',
  },
  sandboxTag: {
    fontSize: '10px',
    background: 'rgba(123,140,255,0.12)',
    border: '1px solid #7b8cff',
    color: '#7b8cff',
    padding: '2px 10px',
    borderRadius: '12px',
  },
  backBtn: {
    marginLeft: 'auto',
    fontSize: '11px',
    background: 'transparent',
    border: '1px solid #444',
    color: '#888',
    padding: '4px 12px',
    borderRadius: '4px',
    cursor: 'pointer',
    fontFamily: 'inherit',
    whiteSpace: 'nowrap',
  },
  // Sandbox body — same 3-col layout, but controls have NO budget-disable rule for full policy
  sandboxBody: {
    display: 'grid',
    gridTemplateColumns: '260px 1fr 300px',
    minHeight: '500px',
  },
  // Mobile: single column
  sandboxBodyMobile: {
    display: 'flex',
    flexDirection: 'column',
  },
  controlsPane: {
    display: 'flex',
    flexDirection: 'column',
    gap: '16px',
    padding: '16px',
    background: '#13131c',
    borderRight: '1px solid #2a2a3a',
    overflowY: 'auto',
  },
  sectionTitle: {
    fontSize: '11px',
    textTransform: 'uppercase',
    letterSpacing: '0.12em',
    color: '#7b8cff',
    borderBottom: '1px solid #2a2a44',
    paddingBottom: '4px',
    marginBottom: '6px',
  },
  policyGrid: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: '4px',
  },
  policyBtn: (selected) => ({
    border: `1px solid ${selected ? '#7b8cff' : '#333'}`,
    background: selected ? 'rgba(123,140,255,0.14)' : '#1a1a26',
    color: selected ? '#c0c8ff' : '#888',
    padding: '9px 6px',
    borderRadius: '4px',
    fontSize: '11px',
    textAlign: 'center',
    cursor: 'pointer',
    lineHeight: 1.3,
    minHeight: '44px', // touch-friendly
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    fontFamily: 'inherit',
  }),
  slider: {
    width: '100%',
    accentColor: '#7b8cff',
    cursor: 'pointer',
    minHeight: '28px', // touch-friendly
  },
  sliderRow: {
    display: 'flex',
    justifyContent: 'space-between',
    fontSize: '11px',
    color: '#aaa',
    marginBottom: '6px',
  },
  sliderVal: { color: '#7b8cff', fontWeight: 600 },
  stepperRow: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
  },
  stepperBtn: {
    width: '44px', height: '44px', // touch-friendly
    border: '1px solid #444',
    background: '#1e1e2e',
    color: '#ccc',
    borderRadius: '4px',
    fontSize: '22px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    cursor: 'pointer',
    fontFamily: 'inherit',
  },
  stepperVal: {
    fontSize: '20px',
    color: '#e0e0f0',
    minWidth: '28px',
    textAlign: 'center',
    fontWeight: 600,
  },
  runBtn: {
    background: '#7b8cff',
    color: '#fff',
    border: 'none',
    borderRadius: '5px',
    padding: '11px 0',
    fontSize: '13px',
    fontWeight: 600,
    cursor: 'pointer',
    width: '100%',
    fontFamily: 'inherit',
    minHeight: '44px',
  },
  centerPane: {
    display: 'flex',
    flexDirection: 'column',
    borderLeft: '1px solid #2a2a3a',
    borderRight: '1px solid #2a2a3a',
    overflowY: 'auto',
  },
  rightPane: {
    display: 'flex',
    flexDirection: 'column',
    background: '#13131c',
    overflowY: 'auto',
    padding: '16px',
    gap: '16px',
  },
  freeplayNote: {
    fontSize: '10px',
    color: '#555',
    fontStyle: 'italic',
  },
};

const POLICIES = [
  { value: 'full',           label: 'Full Cache',    desc: 'No eviction' },
  { value: 'sliding_window', label: 'Sliding Win.',  desc: 'Recency window' },
  { value: 'heavy_hitter',   label: 'Heavy Hitter',  desc: 'Top-k attention' },
  { value: 'bdh_recurrent',  label: 'BDH',           desc: 'Fixed-size state' },
];

/**
 * SandboxControls — same 4 controls as ControlPanel but:
 * 1. Budget is NEVER disabled (even for full policy) — sandbox is free-play
 * 2. Touch-friendly hit targets (minHeight: 44px)
 * 3. No walkthrough narration or step constraints
 */
function SandboxControls() {
  const { state, dispatch, runSimulation } = useSimulation();
  const { cachePolicy, budgetSize, sequenceLength, needleCount } = state.controls;
  const { isLoading } = state.ui;

  const setPolicy = (val) => {
    dispatch({ type: 'SET_CONTROL', payload: { field: 'cachePolicy', value: val } });
    runSimulation({ cachePolicy: val });
  };

  const onBudgetChange = (e) =>
    dispatch({ type: 'SET_CONTROL', payload: { field: 'budgetSize', value: Number(e.target.value) } });
  const onBudgetCommit = (e) => runSimulation({ budgetSize: Number(e.target.value) });

  const onSeqChange = (e) =>
    dispatch({ type: 'SET_CONTROL', payload: { field: 'sequenceLength', value: Number(e.target.value) } });
  const onSeqCommit = (e) => runSimulation({ sequenceLength: Number(e.target.value) });

  const onNeedle = (delta) => {
    const val = Math.min(5, Math.max(1, needleCount + delta));
    dispatch({ type: 'SET_CONTROL', payload: { field: 'needleCount', value: val } });
    runSimulation({ needleCount: val });
  };

  return (
    <div style={s.controlsPane} aria-label="Sandbox simulation controls">
      <div>
        <div style={s.sectionTitle}>Sandbox — Free Play</div>
        <div style={s.freeplayNote}>All controls unlocked. No narration constraints.</div>
      </div>

      {/* Policy */}
      <div>
        <div style={s.sectionTitle}>Cache Policy</div>
        <div style={s.policyGrid} role="radiogroup" aria-label="Cache policy">
          {POLICIES.map(({ value, label, desc }) => (
            <button
              key={value}
              role="radio"
              aria-checked={cachePolicy === value}
              style={s.policyBtn(cachePolicy === value)}
              onClick={() => setPolicy(value)}
              disabled={isLoading}
            >
              <div>{label}</div>
              <div style={{ fontSize: '9px', opacity: 0.7 }}>{desc}</div>
            </button>
          ))}
        </div>
      </div>

      {/* Budget — NEVER disabled in Sandbox */}
      <div>
        <div style={s.sectionTitle}>Budget Size</div>
        <div style={s.sliderRow}>
          <span>8</span>
          <span style={s.sliderVal}>{budgetSize} tokens</span>
          <span>512</span>
        </div>
        <input
          id="sandbox-budget-slider"
          type="range"
          min={8} max={512} step={8}
          value={budgetSize}
          onChange={onBudgetChange}
          onMouseUp={onBudgetCommit}
          onTouchEnd={onBudgetCommit}
          style={s.slider}
          disabled={isLoading}
          aria-label={`Budget size: ${budgetSize} tokens`}
        />
        <div style={{ fontSize: '10px', color: '#555', marginTop: '2px' }}>
          Budget active for all policies in Sandbox mode
        </div>
      </div>

      {/* Sequence Length */}
      <div>
        <div style={s.sectionTitle}>Sequence Length</div>
        <div style={s.sliderRow}>
          <span>32</span>
          <span style={s.sliderVal}>{sequenceLength} tokens</span>
          <span>512</span>
        </div>
        <input
          id="sandbox-seqlen-slider"
          type="range"
          min={32} max={512} step={16}
          value={sequenceLength}
          onChange={onSeqChange}
          onMouseUp={onSeqCommit}
          onTouchEnd={onSeqCommit}
          style={s.slider}
          disabled={isLoading}
          aria-label={`Sequence length: ${sequenceLength} tokens`}
        />
      </div>

      {/* Needle Count */}
      <div>
        <div style={s.sectionTitle}>Needle Count</div>
        <div style={s.stepperRow}>
          <button
            style={s.stepperBtn}
            onClick={() => onNeedle(-1)}
            disabled={needleCount <= 1 || isLoading}
            aria-label="Decrease needle count"
          >−</button>
          <div style={s.stepperVal} aria-live="polite">{needleCount}</div>
          <button
            style={s.stepperBtn}
            onClick={() => onNeedle(1)}
            disabled={needleCount >= 5 || isLoading}
            aria-label="Increase needle count"
          >+</button>
          <span style={{ fontSize: '11px', color: '#888' }}>(1–5)</span>
        </div>
      </div>

      {/* Run */}
      <button
        id="sandbox-run-btn"
        style={isLoading ? { ...s.runBtn, background: '#3a3a5a', cursor: 'not-allowed' } : s.runBtn}
        onClick={() => runSimulation()}
        disabled={isLoading}
        aria-label="Run simulation in sandbox"
      >
        {isLoading ? 'Simulating…' : '▶ Run Simulation'}
      </button>
    </div>
  );
}

/**
 * Sandbox — free-play mode
 *
 * Props:
 *   isUnlocked   {boolean}  Whether sandbox is accessible
 *   onReturnToWalkthrough  {function}  Back to guided flow
 */
function Sandbox({ isUnlocked = false, onReturnToWalkthrough = () => {} }) {
  const { state } = useSimulation();
  const { controls, result, precomputed, ui } = state;
  const showBDH = controls.cachePolicy === 'bdh_recurrent';

  if (!isUnlocked) {
    return (
      <div id="sandbox" style={s.lockedWrapper} aria-label="Sandbox locked">
        <div style={s.lockIcon}>🔒</div>
        <div style={s.lockTitle}>Sandbox Locked</div>
        <div style={s.lockDesc}>
          Complete the guided walkthrough (steps 1–4) to unlock free-play mode,
          where every control is available simultaneously with no constraints.
        </div>
      </div>
    );
  }

  return (
    <div id="sandbox" style={s.sandboxWrapper} aria-label="Sandbox — free-play mode">

      {/* Sandbox header */}
      <div style={s.sandboxHeader}>
        <span style={s.sandboxTitle}>🧪 Sandbox</span>
        <span style={s.sandboxTag}>Free Play — all controls unlocked</span>
        <span style={{ fontSize: '11px', color: '#555', flex: 1 }}>
          Same live backend, no walkthrough constraints
        </span>
        <button
          style={s.backBtn}
          onClick={onReturnToWalkthrough}
          aria-label="Return to guided walkthrough"
        >
          ← Back to walkthrough
        </button>
      </div>

      {/* Error state if any */}
      {ui.errorMessage && (
        <div style={{
          background: '#3a0000', border: '1px solid #ff6b6b',
          color: '#ff6b6b', padding: '6px 16px', fontSize: '12px',
        }}>
          Error: {ui.errorMessage}
        </div>
      )}

      {/* 3-column body — same layout as guided, same data from same store */}
      <div style={s.sandboxBody}>

        {/* Left: controls (all unlocked) */}
        <SandboxControls />

        {/* Center: Heatmap + MemoryChart — same components, same store props */}
        <div style={s.centerPane}>
          <div style={{ padding: '16px', borderBottom: '1px solid #2a2a3a' }}>
            <CacheHeatmap
              aliveTokenIndices={result.aliveTokenIndices}
              sequenceLength={controls.sequenceLength}
              needlePositions={result.needlePositions}
              cachePolicy={controls.cachePolicy}
              isLoading={ui.isLoading}
            />
          </div>
          <div style={{ padding: '16px', flex: 1 }}>
            <MemoryChart
              cacheSizeHistory={result.cacheSizeHistory}
              baselineHistory={result.baselineHistory}
              cachePolicy={controls.cachePolicy}
              sequenceLength={controls.sequenceLength}
              isLoading={ui.isLoading}
            />
          </div>
        </div>

        {/* Right: AccuracyPanel + BDHModule — same components */}
        <div style={s.rightPane}>
          <AccuracyPanel
            modelAnswers={result.modelAnswers}
            correctAnswers={result.correctAnswers}
            liveAccuracyScore={result.accuracyScore}
            currentBudgetSize={controls.budgetSize}
            accuracyVsBudget={precomputed.accuracyVsBudget}
          />
          {showBDH && (
            <BDHModule
              liveStats={{ cacheSizeTokens: result.cacheSizeTokens, accuracyScore: result.accuracyScore }}
              publishedClaims={precomputed.bdhPublishedClaims}
            />
          )}
        </div>
      </div>
    </div>
  );
}

export default Sandbox;
