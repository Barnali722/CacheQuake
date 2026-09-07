/**
 * ControlPanel.jsx
 * Single responsibility: Render and expose the four learner controls —
 * cachePolicy, budgetSize, sequenceLength, and needleCount — per CONTROLS_SPEC §1.1–1.4.
 * Reads from and writes to simulationStore via useSimulation hook.
 */

import React, { useCallback } from 'react';
import { useSimulation } from '../state/simulationStore';

// ─── Policy definitions ────────────────────────────────────────────────────
const POLICIES = [
  { value: 'full',           label: 'Full Cache',     desc: 'No eviction — stores all tokens' },
  { value: 'sliding_window', label: 'Sliding Window', desc: 'StreamingLLM-style window' },
  { value: 'heavy_hitter',   label: 'Heavy Hitter',   desc: 'H2O-style top-k eviction' },
  { value: 'bdh_recurrent',  label: 'BDH Recurrent',  desc: 'Fixed-size overwriting state' },
];

// ─── Styles ──────────────────────────────────────────────────────────────────
const s = {
  panel: {
    display: 'flex',
    flexDirection: 'column',
    gap: '20px',
    padding: '16px',
    background: '#13131c',
    borderRight: '1px solid #2a2a3a',
    overflowY: 'auto',
    minWidth: '240px',
  },
  sectionTitle: {
    fontSize: '11px',
    textTransform: 'uppercase',
    letterSpacing: '0.12em',
    color: '#7b8cff',
    marginBottom: '8px',
    borderBottom: '1px solid #2a2a44',
    paddingBottom: '4px',
  },
  policyGrid: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: '4px',
  },
  policyBtn: (selected, policy) => ({
    border: `1px solid ${selected ? '#7b8cff' : '#333'}`,
    background: selected ? 'rgba(123,140,255,0.14)' : '#1a1a26',
    color: selected ? '#c0c8ff' : '#888',
    padding: '7px 6px',
    borderRadius: '4px',
    fontSize: '11px',
    textAlign: 'center',
    cursor: 'pointer',
    transition: 'all 0.15s ease',
    outline: 'none',
    lineHeight: 1.3,
  }),
  policyBtnDesc: {
    fontSize: '9px',
    opacity: 0.7,
    marginTop: '2px',
  },
  sliderSection: (disabled) => ({
    opacity: disabled ? 0.38 : 1,
    pointerEvents: disabled ? 'none' : 'auto',
    transition: 'opacity 0.2s',
  }),
  sliderLabelRow: {
    display: 'flex',
    justifyContent: 'space-between',
    fontSize: '11px',
    color: '#aaa',
    marginBottom: '6px',
  },
  sliderVal: {
    color: '#7b8cff',
    fontWeight: 600,
  },
  slider: {
    width: '100%',
    accentColor: '#7b8cff',
    cursor: 'pointer',
  },
  stepperRow: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
  },
  stepperBtn: {
    width: '28px',
    height: '28px',
    border: '1px solid #444',
    background: '#1e1e2e',
    color: '#ccc',
    borderRadius: '4px',
    fontSize: '18px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    cursor: 'pointer',
    userSelect: 'none',
    lineHeight: 1,
  },
  stepperVal: {
    fontSize: '18px',
    color: '#e0e0f0',
    minWidth: '24px',
    textAlign: 'center',
    fontWeight: 600,
  },
  runBtn: {
    background: '#7b8cff',
    color: '#fff',
    border: 'none',
    borderRadius: '5px',
    padding: '9px 0',
    fontSize: '13px',
    fontWeight: 600,
    cursor: 'pointer',
    width: '100%',
    letterSpacing: '0.04em',
    transition: 'opacity 0.15s',
  },
  loadingRunBtn: {
    background: '#3a3a5a',
    color: '#888',
    border: 'none',
    borderRadius: '5px',
    padding: '9px 0',
    fontSize: '13px',
    width: '100%',
    cursor: 'not-allowed',
  },
  disabledNote: {
    fontSize: '10px',
    color: '#555',
    marginTop: '4px',
  },
};

/**
 * ControlPanel
 * Reads state from useSimulation(). On any change, immediately dispatches
 * SET_CONTROL to the store, then calls runSimulation() to get new mock data.
 *
 * @see CONTROLS_SPEC.md §1.1–1.4
 */
function ControlPanel() {
  const { state, dispatch, runSimulation } = useSimulation();
  const { cachePolicy, budgetSize, sequenceLength, needleCount } = state.controls;
  const { isLoading } = state.ui;

  const handlePolicyChange = useCallback((val) => {
    dispatch({ type: 'SET_CONTROL', payload: { field: 'cachePolicy', value: val } });
    runSimulation({ cachePolicy: val });
  }, [dispatch, runSimulation]);

  const handleBudgetChange = useCallback((e) => {
    const val = Number(e.target.value);
    dispatch({ type: 'SET_CONTROL', payload: { field: 'budgetSize', value: val } });
  }, [dispatch]);

  const handleBudgetCommit = useCallback((e) => {
    const val = Number(e.target.value);
    runSimulation({ budgetSize: val });
  }, [runSimulation]);

  const handleSeqLenChange = useCallback((e) => {
    const val = Number(e.target.value);
    dispatch({ type: 'SET_CONTROL', payload: { field: 'sequenceLength', value: val } });
  }, [dispatch]);

  const handleSeqLenCommit = useCallback((e) => {
    const val = Number(e.target.value);
    runSimulation({ sequenceLength: val });
  }, [runSimulation]);

  const handleNeedleChange = useCallback((delta) => {
    const val = Math.min(5, Math.max(1, needleCount + delta));
    dispatch({ type: 'SET_CONTROL', payload: { field: 'needleCount', value: val } });
    runSimulation({ needleCount: val });
  }, [dispatch, runSimulation, needleCount]);

  const isBudgetDisabled = cachePolicy === 'full';

  return (
    <div id="control-panel" style={s.panel} aria-label="Simulation Controls">

      {/* ── 1.1 Cache Policy ── */}
      <div>
        <div style={s.sectionTitle}>Cache Policy</div>
        <div style={s.policyGrid} role="radiogroup" aria-label="Cache policy selector">
          {POLICIES.map(({ value, label, desc }) => (
            <button
              key={value}
              role="radio"
              aria-checked={cachePolicy === value}
              onClick={() => handlePolicyChange(value)}
              style={s.policyBtn(cachePolicy === value, value)}
              disabled={isLoading}
            >
              <div>{label}</div>
              <div style={s.policyBtnDesc}>{desc}</div>
            </button>
          ))}
        </div>
        {/* CONTROLS_SPEC §1.1 — cachePolicy → POST /simulate { policy } */}
      </div>

      {/* ── 1.2 Budget Size ── */}
      <div style={s.sliderSection(isBudgetDisabled)}>
        <div style={s.sectionTitle}>
          Budget Size
          {isBudgetDisabled && <span style={{ color: '#555', marginLeft: 6 }}>(n/a for Full Cache)</span>}
        </div>
        <div style={s.sliderLabelRow}>
          <span>8</span>
          <span style={s.sliderVal}>{budgetSize} tokens</span>
          <span>512</span>
        </div>
        <input
          id="budget-slider"
          type="range"
          min={8} max={512} step={8}
          value={budgetSize}
          onChange={handleBudgetChange}
          onMouseUp={handleBudgetCommit}
          onTouchEnd={handleBudgetCommit}
          style={s.slider}
          disabled={isBudgetDisabled || isLoading}
          aria-label={`Budget size: ${budgetSize} tokens`}
          aria-disabled={isBudgetDisabled}
        />
        {isBudgetDisabled && (
          <div style={s.disabledNote}>Enable eviction policy to use budget control.</div>
        )}
        {/* CONTROLS_SPEC §1.2 — budgetSize → POST /simulate { budget } */}
      </div>

      {/* ── 1.3 Sequence Length ── */}
      <div>
        <div style={s.sectionTitle}>Sequence Length</div>
        <div style={s.sliderLabelRow}>
          <span>32</span>
          <span style={s.sliderVal}>{sequenceLength} tokens</span>
          <span>512</span>
        </div>
        <input
          id="seqlen-slider"
          type="range"
          min={32} max={512} step={16}
          value={sequenceLength}
          onChange={handleSeqLenChange}
          onMouseUp={handleSeqLenCommit}
          onTouchEnd={handleSeqLenCommit}
          style={s.slider}
          disabled={isLoading}
          aria-label={`Sequence length: ${sequenceLength} tokens`}
        />
        {/* CONTROLS_SPEC §1.3 — sequenceLength → POST /simulate { seq_len } */}
      </div>

      {/* ── 1.4 Needle Count ── */}
      <div>
        <div style={s.sectionTitle}>Needle Count</div>
        <div style={s.stepperRow}>
          <button
            onClick={() => handleNeedleChange(-1)}
            style={s.stepperBtn}
            disabled={needleCount <= 1 || isLoading}
            aria-label="Decrease needle count"
          >
            −
          </button>
          <div style={s.stepperVal} aria-live="polite">{needleCount}</div>
          <button
            onClick={() => handleNeedleChange(1)}
            style={s.stepperBtn}
            disabled={needleCount >= 5 || isLoading}
            aria-label="Increase needle count"
          >
            +
          </button>
          <span style={{ fontSize: '11px', color: '#888' }}>needle{needleCount !== 1 ? 's' : ''} (1–5)</span>
        </div>
        {/* CONTROLS_SPEC §1.4 — needleCount → POST /simulate { num_needles } */}
      </div>

      {/* ── Manual Run button (for when sliders don't auto-trigger) ── */}
      <button
        onClick={() => runSimulation()}
        style={isLoading ? s.loadingRunBtn : s.runBtn}
        disabled={isLoading}
        aria-label="Run simulation"
      >
        {isLoading ? 'Simulating…' : '▶ Run Simulation'}
      </button>

    </div>
  );
}

export default ControlPanel;
