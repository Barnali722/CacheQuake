/**
 * MemoryChart.jsx
 * Single responsibility: Plot live memory footprint (cache_size_tokens) against
 * the full-cache baseline (full_cache_baseline_tokens) over generation steps,
 * per CONTROLS_SPEC §2.1.
 */

import React from 'react';

/**
 * MemoryChart
 *
 * Props:
 *   memoryUsedHistory    {number[]}  Per-step cache_size_tokens values from /simulate
 *   memoryBaselineHistory {number[]} Per-step full_cache_baseline_tokens values from /simulate
 *   currentStep          {number}    Current generation step index (for cursor indicator)
 *
 * Both props sourced from the live /simulate response — no PrecomputedBadge on this component.
 *
 * @see CONTROLS_SPEC.md §2.1
 */
function MemoryChart({
  memoryUsedHistory = [],
  memoryBaselineHistory = [],
  currentStep = 0,
}) {
  return (
    <div id="memory-chart" aria-label="Memory footprint: live policy vs. full-cache baseline">
      {/* ── Not yet implemented placeholder ── */}
      <div>MemoryChart — not yet implemented</div>

      {/*
        Day 2 implementation notes:
        - Render a two-line chart (e.g. recharts LineChart or lightweight canvas).
        - Line 1 (colored): memoryUsedHistory — labeled "Live policy".
        - Line 2 (dashed grey): memoryBaselineHistory — labeled "Full-cache baseline".
        - X-axis: generation step. Y-axis: tokens in cache.
        - Both data arrays come from the live /simulate call — no PrecomputedBadge.
        - Show ratio live/baseline as a small numeric readout (e.g. "saves 58%").
      */}
    </div>
  );
}

export default MemoryChart;
