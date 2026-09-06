/**
 * CacheHeatmap.jsx
 * Single responsibility: Visualise which token positions are currently "alive"
 * in the KV cache (aliveTokenIndices) versus the full-cache baseline,
 * per CONTROLS_SPEC §2.4.
 *
 * Data contract: all props come from simulationStore (live API response) — never hardcoded.
 * All four policies produce visibly distinct cell patterns; see POLICY_DESCRIPTIONS below.
 */

import React, { useMemo } from 'react';

// ─── Styles ──────────────────────────────────────────────────────────────────
const styles = {
  wrapper: {
    display: 'flex',
    flexDirection: 'column',
    gap: '10px',
    padding: '0',
  },
  rowLabel: {
    fontSize: '10px',
    textTransform: 'uppercase',
    letterSpacing: '0.1em',
    color: '#666680',
    marginBottom: '3px',
  },
  grid: {
    display: 'grid',
    gap: '2px',
  },
  legend: {
    display: 'flex',
    gap: '16px',
    marginTop: '6px',
    flexWrap: 'wrap',
  },
  legendItem: {
    display: 'flex',
    alignItems: 'center',
    gap: '5px',
    fontSize: '10px',
    color: '#aaaacc',
  },
  legendDot: {
    width: '10px',
    height: '10px',
    borderRadius: '2px',
    flexShrink: 0,
  },
  liveLabel: {
    display: 'inline-block',
    background: '#001f0f',
    border: '1px solid #3dffa0',
    color: '#3dffa0',
    fontSize: '10px',
    padding: '2px 8px',
    borderRadius: '3px',
    marginLeft: '6px',
    verticalAlign: 'middle',
  },
  statsRow: {
    display: 'flex',
    gap: '16px',
    fontSize: '11px',
    color: '#aaaacc',
    marginTop: '4px',
  },
  statBold: {
    color: '#e0e0f0',
    fontWeight: '600',
  },
  divider: {
    borderTop: '1px solid #2a2a3a',
    margin: '6px 0',
  },
  vsLabel: {
    fontSize: '10px',
    color: '#555',
    textAlign: 'center',
    margin: '2px 0',
  },
};

// ── Per-policy descriptions (Agent 2: ensures each policy is visually annotated) ──
const POLICY_DESCRIPTIONS = {
  full:
    'Full Cache — every token is stored. No eviction. Memory grows linearly with sequence length.',
  sliding_window:
    'Sliding Window — keeps only the most recent \u0060budget\u0060 tokens. Old tokens are evicted from the left. Simple but loses long-range context.',
  heavy_hitter:
    'Heavy Hitter (H2O) — keeps the \u0060budget\u0060 tokens with the highest cumulative attention score. Needle tokens score high and tend to survive; filler tokens are evicted.',
  bdh_recurrent:
    'BDH Recurrent — a fixed-size state that overwrites itself as new tokens arrive. Memory never grows (O(1)), but information is lost via interference, not eviction.',
};

// Cell color map
const CELL_COLORS = {
  needle_alive:   '#ff6b6b',  // needle AND in cache — highlight
  needle_evicted: '#7a2020',  // needle evicted — critical loss
  alive:          '#3dffa0',  // normal token, in cache
  evicted:        '#1e1e2e',  // normal token, evicted
  baseline:       '#2a3a2a',  // baseline row — all alive, softer green
  baseline_needle:'#ff6b6b',  // needle in baseline row
};

/**
 * Single token cell.
 */
function HeatCell({ state, tokenIndex }) {
  const color =
    state === 'needle_alive'   ? CELL_COLORS.needle_alive :
    state === 'needle_evicted' ? CELL_COLORS.needle_evicted :
    state === 'alive'          ? CELL_COLORS.alive :
    state === 'baseline'       ? CELL_COLORS.baseline :
    state === 'baseline_needle'? CELL_COLORS.baseline_needle :
                                 CELL_COLORS.evicted;

  return (
    <div
      title={`Token ${tokenIndex}: ${state}`}
      aria-label={`Token ${tokenIndex}: ${state}`}
      style={{
        background: color,
        borderRadius: '2px',
        transition: 'background 0.25s ease',
        aspectRatio: '1',
        minWidth: 0,
      }}
    />
  );
}

/**
 * CacheHeatmap
 *
 * Props:
 *   aliveTokenIndices  {number[]}  Indices of tokens still in cache — from /simulate response
 *   sequenceLength     {number}    Total sequence length — determines grid columns
 *   needlePositions    {number[]}  Token indices that are needle facts
 *   cachePolicy        {string}    Active policy — drives annotation text
 *   isLoading          {boolean}   Show loading state while simulation is in-flight
 *
 * @see CONTROLS_SPEC.md §2.4
 */
function CacheHeatmap({
  aliveTokenIndices = [],
  sequenceLength = 128,
  needlePositions = [],
  cachePolicy = 'full',
  isLoading = false,
}) {
  // Number of grid columns — cap at 64 for readability, group wider sequences
  const cols = useMemo(() => {
    if (sequenceLength <= 64)  return sequenceLength;
    if (sequenceLength <= 128) return 64;
    return 64; // always 64 columns max; multiple rows for longer seqs
  }, [sequenceLength]);

  const aliveSet  = useMemo(() => new Set(aliveTokenIndices), [aliveTokenIndices]);
  const needleSet = useMemo(() => new Set(needlePositions),   [needlePositions]);

  const aliveCount   = aliveTokenIndices.length;
  const evictedCount = sequenceLength - aliveCount;
  const needlesAlive = needlePositions.filter((n) => aliveSet.has(n)).length;

  // Build cell state arrays
  const policyCells = useMemo(() =>
    Array.from({ length: sequenceLength }, (_, i) => {
      const isNeedle = needleSet.has(i);
      const isAlive  = aliveSet.has(i);
      if (isNeedle && isAlive)  return 'needle_alive';
      if (isNeedle && !isAlive) return 'needle_evicted';
      return isAlive ? 'alive' : 'evicted';
    }),
    [sequenceLength, aliveSet, needleSet]
  );

  const baselineCells = useMemo(() =>
    Array.from({ length: sequenceLength }, (_, i) =>
      needleSet.has(i) ? 'baseline_needle' : 'baseline'
    ),
    [sequenceLength, needleSet]
  );

  if (isLoading) {
    return (
      <div style={{ color: '#666680', fontSize: '12px', padding: '12px' }}>
        Simulating…
      </div>
    );
  }

  return (
    <div id="cache-heatmap" style={styles.wrapper} aria-label="Cache Heatmap — live vs. full-cache baseline">

      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
        <span style={{ fontSize: '12px', color: '#e0e0f0', fontWeight: 600 }}>
          Token Cache State
        </span>
        <span style={styles.liveLabel}>LIVE</span>
        <span style={{
          fontSize: '10px', color: '#aaa',
          background: '#1a1a28', border: '1px solid #333',
          borderRadius: '3px', padding: '1px 8px',
        }}>
          {cachePolicy.replace('_', ' ').replace(/\b\w/g, c => c.toUpperCase())}
        </span>
      </div>

      {/* Per-policy annotation — Agent 2: makes each policy visually distinct */}
      <div style={{
        fontSize: '11px', color: '#8888aa', lineHeight: 1.5,
        background: '#13131c', border: '1px solid #2a2a3a',
        borderRadius: '4px', padding: '6px 10px',
      }}>
        {POLICY_DESCRIPTIONS[cachePolicy] || 'Unknown policy.'}
      </div>

      {/* Stats row */}
      <div style={styles.statsRow}>
        <span>In cache: <span style={styles.statBold}>{aliveCount}</span></span>
        <span>Evicted: <span style={styles.statBold}>{evictedCount}</span></span>
        <span>
          Needles retained:{' '}
          <span style={{ ...styles.statBold, color: needlesAlive === needlePositions.length ? '#3dffa0' : '#ff6b6b' }}>
            {needlesAlive}/{needlePositions.length}
          </span>
        </span>
      </div>

      {/* Policy row — current cache state */}
      <div>
        <div style={styles.rowLabel}>Current policy ↓</div>
        <div style={{ ...styles.grid, gridTemplateColumns: `repeat(${cols}, 1fr)` }}>
          {policyCells.map((state, i) => (
            <HeatCell key={i} state={state} tokenIndex={i} />
          ))}
        </div>
      </div>

      {/* Divider */}
      <div style={styles.vsLabel}>vs. Full Cache baseline</div>

      {/* Baseline row — all tokens alive */}
      <div>
        <div style={styles.rowLabel}>Full cache baseline — all alive ↓</div>
        <div style={{ ...styles.grid, gridTemplateColumns: `repeat(${cols}, 1fr)` }}>
          {baselineCells.map((state, i) => (
            <HeatCell key={i} state={state} tokenIndex={i} />
          ))}
        </div>
      </div>

      {/* Legend */}
      <div style={styles.legend}>
        {[
          { color: CELL_COLORS.alive,          label: 'In cache' },
          { color: CELL_COLORS.evicted,        label: 'Evicted' },
          { color: CELL_COLORS.needle_alive,   label: 'Needle (in cache)' },
          { color: CELL_COLORS.needle_evicted, label: 'Needle (evicted!)' },
        ].map(({ color, label }) => (
          <div key={label} style={styles.legendItem}>
            <div style={{ ...styles.legendDot, background: color }} />
            <span>{label}</span>
          </div>
        ))}
      </div>

      <div style={{ fontSize: '10px', color: '#555', marginTop: '2px' }}>
        Live cache state — per CONTROLS_SPEC §2.4
      </div>
    </div>
  );
}

export default CacheHeatmap;
