/**
 * MemoryChart.jsx
 * Single responsibility: Plot live memory footprint (cache_size_tokens per step)
 * against the full-cache baseline (full_cache_baseline_tokens per step),
 * per CONTROLS_SPEC §2.1.
 *
 * Uses a lightweight canvas-based SVG chart — no external chart library needed.
 * Day 3: same props, same render logic — only the data source changes (mock → live API).
 */

import React, { useMemo } from 'react';

// ─── Styles ──────────────────────────────────────────────────────────────────
const CHART_H = 160;
const CHART_PAD = { top: 12, right: 16, bottom: 28, left: 44 };

const styles = {
  wrapper: {
    display: 'flex',
    flexDirection: 'column',
    gap: '8px',
  },
  header: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
  },
  title: {
    fontSize: '12px',
    color: '#e0e0f0',
    fontWeight: 600,
  },
  liveLabel: {
    display: 'inline-block',
    background: '#001f0f',
    border: '1px solid #3dffa0',
    color: '#3dffa0',
    fontSize: '10px',
    padding: '2px 8px',
    borderRadius: '3px',
  },
  mockLabel: {
    fontSize: '10px',
    color: '#f5a623',
    background: '#1a1000',
    border: '1px solid #f5a623',
    borderRadius: '3px',
    padding: '1px 6px',
  },
  chartBox: {
    background: '#0d0d12',
    border: '1px solid #2a2a3a',
    borderRadius: '6px',
    overflow: 'hidden',
    width: '100%',
  },
  legendRow: {
    display: 'flex',
    gap: '16px',
    flexWrap: 'wrap',
  },
  legendItem: {
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
    fontSize: '10px',
    color: '#aaaacc',
  },
  statsRow: {
    display: 'flex',
    gap: '20px',
    fontSize: '11px',
    color: '#aaaacc',
    flexWrap: 'wrap',
  },
  bold: {
    color: '#e0e0f0',
    fontWeight: 600,
  },
};

// Policy → chart line color
const POLICY_COLOR = {
  full:           '#7b8cff',
  sliding_window: '#3dffa0',
  heavy_hitter:   '#ffb347',
  bdh_recurrent:  '#c084fc',
};

/**
 * Normalize an array of values to SVG coordinates within the chart area.
 */
function toSVGPoints(values, maxVal, chartW, chartH, pad) {
  if (!values || values.length === 0) return '';
  const usableW = chartW - pad.left - pad.right;
  const usableH = chartH - pad.top - pad.bottom;
  return values
    .map((v, i) => {
      const x = pad.left + (i / Math.max(values.length - 1, 1)) * usableW;
      const y = pad.top + usableH - (v / maxVal) * usableH;
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(' ');
}

/**
 * MemoryChart
 *
 * Props:
 *   cacheSizeHistory    {number[]}  Per-step cache_size_tokens — from /simulate response
 *   baselineHistory     {number[]}  Per-step full_cache_baseline_tokens — from /simulate response
 *   cachePolicy         {string}    Current policy — drives line color
 *   sequenceLength      {number}    Total steps on X axis
 *   isLoading           {boolean}   Show placeholder while simulating
 *
 * @see CONTROLS_SPEC.md §2.1
 */
function MemoryChart({
  cacheSizeHistory = [],
  baselineHistory = [],
  cachePolicy = 'full',
  sequenceLength = 128,
  isLoading = false,
}) {
  const lineColor = POLICY_COLOR[cachePolicy] || '#7b8cff';

  // Compute chart dimensions responsively using a fixed aspect ratio
  const chartW = 560; // SVG viewBox width (scales via CSS width:100%)
  const chartH_total = CHART_H;
  const pad = CHART_PAD;
  const usableW = chartW - pad.left - pad.right;
  const usableH = chartH_total - pad.top - pad.bottom;

  const maxVal = useMemo(() => {
    const allVals = [...cacheSizeHistory, ...baselineHistory];
    return Math.max(...allVals, sequenceLength, 1);
  }, [cacheSizeHistory, baselineHistory, sequenceLength]);

  const policyPoints   = useMemo(() => toSVGPoints(cacheSizeHistory, maxVal, chartW, chartH_total, pad), [cacheSizeHistory, maxVal]);
  const baselinePoints = useMemo(() => toSVGPoints(baselineHistory,  maxVal, chartW, chartH_total, pad), [baselineHistory,  maxVal]);

  // Stats
  const lastLive     = cacheSizeHistory[cacheSizeHistory.length - 1] ?? 0;
  const lastBaseline = baselineHistory[baselineHistory.length - 1]   ?? sequenceLength;
  const savingsPct   = lastBaseline > 0 ? Math.round((1 - lastLive / lastBaseline) * 100) : 0;

  // Y-axis tick labels
  const yTicks = [0, 0.25, 0.5, 0.75, 1].map((frac) => ({
    val: Math.round(frac * maxVal),
    y:   pad.top + usableH - frac * usableH,
  }));

  // X-axis tick labels
  const xTicks = [0, 0.25, 0.5, 0.75, 1].map((frac) => ({
    val: Math.round(frac * sequenceLength),
    x:   pad.left + frac * usableW,
  }));

  if (isLoading) {
    return (
      <div style={{ color: '#666680', fontSize: '12px', padding: '12px' }}>
        Simulating…
      </div>
    );
  }

  const hasData = cacheSizeHistory.length > 0;

  return (
    <div id="memory-chart" style={styles.wrapper} aria-label="Memory footprint: live policy vs. full-cache baseline">

      {/* Header */}
      <div style={styles.header}>
        <span style={styles.title}>Memory Footprint</span>
        <span style={styles.liveLabel}>LIVE</span>
      </div>

      {/* Stats */}
      <div style={styles.statsRow}>
        <span>Policy cache size: <span style={{ ...styles.bold, color: lineColor }}>{lastLive} tokens</span></span>
        <span>Full-cache baseline: <span style={styles.bold}>{lastBaseline} tokens</span></span>
        {cachePolicy !== 'full' && (
          <span>
            Memory saved:{' '}
            <span style={{ ...styles.bold, color: savingsPct > 0 ? '#3dffa0' : '#aaa' }}>
              {savingsPct}%
            </span>
          </span>
        )}
      </div>

      {/* SVG Chart */}
      <div style={styles.chartBox}>
        <svg
          viewBox={`0 0 ${chartW} ${chartH_total}`}
          style={{ width: '100%', display: 'block' }}
          aria-hidden="true"
        >
          {/* Grid lines */}
          {yTicks.map(({ y, val }) => (
            <g key={val}>
              <line
                x1={pad.left} y1={y} x2={chartW - pad.right} y2={y}
                stroke="#1e1e2e" strokeWidth="1"
              />
              <text x={pad.left - 6} y={y + 4} textAnchor="end" fill="#555" fontSize="9">
                {val}
              </text>
            </g>
          ))}

          {/* X axis ticks */}
          {xTicks.map(({ x, val }) => (
            <text key={val} x={x} y={chartH_total - 4} textAnchor="middle" fill="#555" fontSize="9">
              {val}
            </text>
          ))}

          {/* Axis labels */}
          <text x={pad.left - 34} y={pad.top + usableH / 2} textAnchor="middle"
                fill="#666" fontSize="9"
                transform={`rotate(-90, ${pad.left - 34}, ${pad.top + usableH / 2})`}>
            Tokens in cache
          </text>
          <text x={pad.left + usableW / 2} y={chartH_total - 1} textAnchor="middle" fill="#666" fontSize="9">
            Generation step
          </text>

          {/* Axes */}
          <line x1={pad.left} y1={pad.top} x2={pad.left} y2={pad.top + usableH} stroke="#333" strokeWidth="1" />
          <line x1={pad.left} y1={pad.top + usableH} x2={chartW - pad.right} y2={pad.top + usableH} stroke="#333" strokeWidth="1" />

          {/* Baseline line (dashed grey) */}
          {hasData && (
            <polyline
              points={baselinePoints}
              fill="none"
              stroke="#555"
              strokeWidth="1.5"
              strokeDasharray="5,4"
            />
          )}

          {/* Policy line (colored) */}
          {hasData && (
            <polyline
              points={policyPoints}
              fill="none"
              stroke={lineColor}
              strokeWidth="2"
              strokeLinejoin="round"
            />
          )}

          {/* Current endpoint dot */}
          {hasData && (() => {
            const lastIdx = cacheSizeHistory.length - 1;
            const x = pad.left + (lastIdx / Math.max(cacheSizeHistory.length - 1, 1)) * usableW;
            const y = pad.top + usableH - (lastLive / maxVal) * usableH;
            return <circle cx={x} cy={y} r="4" fill={lineColor} />;
          })()}

          {/* Empty state */}
          {!hasData && (
            <text x={chartW / 2} y={chartH_total / 2} textAnchor="middle" fill="#444" fontSize="12">
              Run a simulation to see data
            </text>
          )}
        </svg>
      </div>

      {/* Legend */}
      <div style={styles.legendRow}>
        <div style={styles.legendItem}>
          <svg width="20" height="10">
            <line x1="0" y1="5" x2="20" y2="5" stroke={lineColor} strokeWidth="2" />
          </svg>
          <span>Live policy ({cachePolicy.replace('_', ' ')})</span>
        </div>
        <div style={styles.legendItem}>
          <svg width="20" height="10">
            <line x1="0" y1="5" x2="20" y2="5" stroke="#555" strokeWidth="1.5" strokeDasharray="4,3" />
          </svg>
          <span>Full-cache baseline (reference)</span>
        </div>
      </div>

      <div style={{ fontSize: '10px', color: '#555' }}>
        Live — computed this run · CONTROLS_SPEC §2.1
      </div>
    </div>
  );
}

export default MemoryChart;
