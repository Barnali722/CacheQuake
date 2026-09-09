/**
 * AccuracyPanel.jsx
 * Single responsibility: Display needle retrieval accuracy — model_answers[] vs.
 * ground_truth_answers[] (live), plus the precomputed accuracy-vs-budget curve
 * with a PrecomputedBadge, per CONTROLS_SPEC §2.2 and §2.3.
 *
 * Every readout shows a live value beside its ground-truth/baseline counterpart.
 * Both sourced entirely from the live API response — no hardcoded comparison numbers.
 */

import React, { useMemo } from 'react';
import PrecomputedBadge from './PrecomputedBadge';

// ─── Chart dimensions ────────────────────────────────────────────────────────
const CURVE_W = 280;
const CURVE_H = 90;
const PAD = { top: 8, right: 12, bottom: 22, left: 36 };

// ─── Styles ──────────────────────────────────────────────────────────────────
const s = {
  wrapper: {
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
  },
  header: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
  },
  title: { fontSize: '12px', color: '#e0e0f0', fontWeight: 600 },
  liveLabel: {
    display: 'inline-block',
    background: '#001f0f',
    border: '1px solid #3dffa0',
    color: '#3dffa0',
    fontSize: '10px',
    padding: '2px 8px',
    borderRadius: '3px',
  },
  scoreRow: {
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
    fontSize: '12px',
    color: '#aaaacc',
  },
  scoreBig: (val) => ({
    fontSize: '22px',
    fontWeight: 700,
    color: val >= 0.8 ? '#3dffa0' : val >= 0.5 ? '#ffb347' : '#ff6b6b',
  }),
  tableHeader: {
    display: 'grid',
    gridTemplateColumns: '28px 1fr 1fr',
    gap: '4px',
    fontSize: '10px',
    textTransform: 'uppercase',
    letterSpacing: '0.08em',
    color: '#666',
    padding: '0 4px',
    marginBottom: '2px',
  },
  needleRow: {
    display: 'grid',
    gridTemplateColumns: '28px 1fr 1fr',
    gap: '4px',
    padding: '4px',
    borderRadius: '4px',
    background: '#13131c',
    marginBottom: '3px',
    alignItems: 'center',
    fontSize: '11px',
  },
  answerChip: (correct) => ({
    padding: '2px 8px',
    borderRadius: '3px',
    background: correct ? 'rgba(61,255,160,0.1)' : 'rgba(255,107,107,0.1)',
    border: `1px solid ${correct ? '#3dffa0' : '#ff6b6b'}`,
    color: correct ? '#3dffa0' : '#ff6b6b',
    fontSize: '10px',
    fontFamily: 'monospace',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    whiteSpace: 'nowrap',
  }),
  correctChip: {
    padding: '2px 8px',
    borderRadius: '3px',
    background: 'rgba(123,140,255,0.1)',
    border: '1px solid #7b8cff',
    color: '#c0c8ff',
    fontSize: '10px',
    fontFamily: 'monospace',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    whiteSpace: 'nowrap',
  },
  curveSection: {
    borderTop: '1px solid #2a2a3a',
    paddingTop: '10px',
  },
  curveTitleRow: {
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
    marginBottom: '6px',
    fontSize: '11px',
    color: '#ccc',
    flexWrap: 'wrap',
  },
  chartBox: {
    background: '#0d0d12',
    border: '1px solid #2a2a3a',
    borderRadius: '5px',
    overflow: 'hidden',
  },
  emptyNote: {
    fontSize: '10px',
    color: '#555',
    padding: '8px 0',
  },
};

/**
 * AccuracyPanel
 *
 * Props:
 *   modelAnswers        {string[]}  Live — from /simulate { model_answers }
 *   correctAnswers      {string[]}  Ground truth — from /simulate { ground_truth_answers }
 *   liveAccuracyScore   {number}    Live — from /simulate { accuracy_score }
 *   currentBudgetSize   {number}    Current budget for live dot placement on curve
 *   accuracyVsBudget    {object[]}  Precomputed curve [{budget, accuracy}] — from accuracy_vs_budget.json
 *
 * @see CONTROLS_SPEC.md §2.2, §2.3
 */
function AccuracyPanel({
  modelAnswers = [],
  correctAnswers = [],
  liveAccuracyScore = null,
  currentBudgetSize = 64,
  accuracyVsBudget = [],
}) {
  const pct = liveAccuracyScore !== null ? Math.round(liveAccuracyScore * 100) : null;

  // Build curve SVG points from precomputed data
  const { curvePoints, livePoint } = useMemo(() => {
    if (!accuracyVsBudget || accuracyVsBudget.length === 0) {
      return { curvePoints: '', livePoint: null };
    }

    const usableW = CURVE_W - PAD.left - PAD.right;
    const usableH = CURVE_H - PAD.top - PAD.bottom;
    const maxBudget = Math.max(...accuracyVsBudget.map((d) => d.budget), currentBudgetSize, 1);

    const pts = accuracyVsBudget
      .map(({ budget, accuracy }) => {
        const x = PAD.left + (budget / maxBudget) * usableW;
        const y = PAD.top + usableH - accuracy * usableH;
        return `${x.toFixed(1)},${y.toFixed(1)}`;
      })
      .join(' ');

    // Live dot position
    const lx = PAD.left + (currentBudgetSize / maxBudget) * usableW;
    const ly =
      liveAccuracyScore !== null
        ? PAD.top + usableH - liveAccuracyScore * usableH
        : null;

    return {
      curvePoints: pts,
      livePoint: ly !== null ? { x: lx, y: ly } : null,
    };
  }, [accuracyVsBudget, currentBudgetSize, liveAccuracyScore]);

  const hasData = modelAnswers.length > 0;
  const hasCurve = accuracyVsBudget.length > 0;

  return (
    <div id="accuracy-panel" style={s.wrapper} aria-label="Needle retrieval accuracy">

      {/* ── Section A header ── */}
      <div style={s.header}>
        <span style={s.title}>Needle Retrieval Accuracy</span>
        <span style={s.liveLabel}>LIVE</span>
      </div>

      {/* ── Overall score ── */}
      {pct !== null && (
        <div style={s.scoreRow}>
          <span style={s.scoreBig(liveAccuracyScore)}>{pct}%</span>
          <span>
            {modelAnswers.filter((a, i) => a === correctAnswers[i]).length} of{' '}
            {correctAnswers.length} needles correctly retrieved
          </span>
        </div>
      )}

      {/* ── Section A: Needle table (CONTROLS_SPEC §2.2) ── */}
      {hasData ? (
        <>
          <div style={s.tableHeader}>
            <span>#</span>
            <span>Model output</span>
            <span>Correct answer</span>
          </div>
          {correctAnswers.map((correct, i) => {
            const model = modelAnswers[i] ?? '—';
            // Model predicts first character only, so compare first char of ground truth
            const isCorrect = model && correct && model === correct[0];
            return (
              <div key={i} style={s.needleRow}>
                <span style={{ fontSize: '10px', color: '#555', textAlign: 'center' }}>
                  {i + 1}
                </span>
                <div style={s.answerChip(isCorrect)} title={`Model predicted: ${model}`}>
                  {isCorrect ? '✓ ' : '✗ '}{model}
                </div>
                <div style={s.correctChip} title={`Full answer: ${correct}`}>
                  {correct}
                </div>
              </div>
            );
          })}
        </>
      ) : (
        <div style={s.emptyNote}>Run a simulation to see needle retrieval results.</div>
      )}

      {/* ── Section B: Accuracy-vs-budget curve (CONTROLS_SPEC §2.3) ── */}
      <div style={s.curveSection}>
        <div style={s.curveTitleRow}>
          <span>Accuracy vs. Budget</span>
          {/* CONTROLS_SPEC §3 placement #1 — mandatory PrecomputedBadge on the curve */}
          <PrecomputedBadge text="Precomputed sweep — not this run" />
        </div>

        {hasCurve ? (
          <div style={s.chartBox}>
            <svg
              viewBox={`0 0 ${CURVE_W} ${CURVE_H}`}
              style={{ width: '100%', display: 'block' }}
              aria-hidden="true"
            >
              {/* Axes */}
              <line
                x1={PAD.left} y1={PAD.top}
                x2={PAD.left} y2={PAD.top + (CURVE_H - PAD.top - PAD.bottom)}
                stroke="#333" strokeWidth="0.8"
              />
              <line
                x1={PAD.left} y1={PAD.top + (CURVE_H - PAD.top - PAD.bottom)}
                x2={CURVE_W - PAD.right} y2={PAD.top + (CURVE_H - PAD.top - PAD.bottom)}
                stroke="#333" strokeWidth="0.8"
              />

              {/* 50% grid line */}
              {(() => {
                const usableH = CURVE_H - PAD.top - PAD.bottom;
                const y50 = PAD.top + usableH * 0.5;
                return (
                  <>
                    <line x1={PAD.left} y1={y50} x2={CURVE_W - PAD.right} y2={y50}
                          stroke="#1e1e2e" strokeWidth="0.8" strokeDasharray="3,3" />
                    <text x={PAD.left - 4} y={y50 + 3} textAnchor="end" fill="#444" fontSize="8">50%</text>
                  </>
                );
              })()}

              {/* Axis labels */}
              <text x={PAD.left - 4} y={PAD.top + 3} textAnchor="end" fill="#444" fontSize="8">100%</text>
              <text x={PAD.left + 2} y={CURVE_H - 4} textAnchor="start" fill="#444" fontSize="8">Budget →</text>

              {/* Precomputed curve (orange) */}
              <polyline
                points={curvePoints}
                fill="none"
                stroke="#f5a623"
                strokeWidth="1.5"
                opacity="0.8"
              />

              {/* Live point (blue dot) — from current run */}
              {livePoint && (
                <>
                  <circle cx={livePoint.x} cy={livePoint.y} r="4" fill="#7b8cff" />
                  <text x={livePoint.x + 6} y={livePoint.y + 4} fill="#7b8cff" fontSize="8">
                    Current
                  </text>
                </>
              )}
            </svg>
          </div>
        ) : (
          <div style={s.emptyNote}>
            Precomputed curve not yet loaded — check backend /data/precomputed/ endpoint.
          </div>
        )}

        {/* Legend */}
        <div style={{ display: 'flex', gap: '12px', marginTop: '4px', flexWrap: 'wrap' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '5px', fontSize: '10px', color: '#aaa' }}>
            <div style={{ width: 14, height: 2, background: '#f5a623' }} />
            <span>Precomputed sweep</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '5px', fontSize: '10px', color: '#aaa' }}>
            <div style={{ width: 8, height: 8, borderRadius: '50%', background: '#7b8cff' }} />
            <span>This run ({currentBudgetSize} tok)</span>
          </div>
        </div>
      </div>

    </div>
  );
}

export default AccuracyPanel;
