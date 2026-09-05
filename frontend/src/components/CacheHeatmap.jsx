/**
 * CacheHeatmap.jsx
 * Single responsibility: Visualise which token positions are currently "alive"
 * in the KV cache (aliveTokenIndices) versus the full-cache baseline,
 * per CONTROLS_SPEC §2.4.
 */

import React from 'react';

/**
 * CacheHeatmap
 *
 * Props:
 *   aliveTokenIndices  {number[]}  Indices of tokens still in cache — from /simulate { alive_token_indices }
 *   sequenceLength     {number}    Total tokens in the sequence — determines grid width
 *   needlePositions    {number[]}  Token indices that are needle facts (always highlighted)
 *   isLive             {boolean}   True when data comes from a live /simulate call (drives badge)
 *
 * @see CONTROLS_SPEC.md §2.4
 */
function CacheHeatmap({
  aliveTokenIndices = [],
  sequenceLength = 128,
  needlePositions = [],
  isLive = false,
}) {
  return (
    <div id="cache-heatmap" aria-label="Cache Heatmap — live vs. full-cache baseline">
      {/* ── Not yet implemented placeholder ── */}
      <div>CacheHeatmap — not yet implemented</div>

      {/*
        Day 2 implementation notes:
        - Render two rows of cells: current policy (top) vs. all-alive baseline (bottom).
        - Cell states: alive (green), evicted (dark grey), needle (red/highlight).
        - aliveTokenIndices sourced from /simulate response field alive_token_indices[].
        - No PrecomputedBadge on this component — all data is live.
        - Render "Live cache state" label below grid.
      */}
    </div>
  );
}

export default CacheHeatmap;
