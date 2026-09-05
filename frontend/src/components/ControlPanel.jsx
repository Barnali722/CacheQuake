/**
 * ControlPanel.jsx
 * Single responsibility: Render and expose the four learner controls —
 * cachePolicy, budgetSize, sequenceLength, and needleCount — per CONTROLS_SPEC §1.1–1.4.
 */

import React from 'react';

/**
 * ControlPanel
 *
 * Props (all controlled — state lives in simulationStore):
 *   cachePolicy     {string}   "full" | "sliding_window" | "heavy_hitter" | "bdh_recurrent"
 *   budgetSize      {number}   integer 8–512, step 8
 *   sequenceLength  {number}   integer 32–512, step 16
 *   needleCount     {number}   integer 1–5
 *   onChange        {function} (fieldName, newValue) => void
 *
 * @see CONTROLS_SPEC.md §1.1, §1.2, §1.3, §1.4
 */
function ControlPanel({
  cachePolicy = 'full',
  budgetSize = 64,
  sequenceLength = 128,
  needleCount = 2,
  onChange = () => {},
}) {
  const POLICIES = [
    { value: 'full',           label: 'Full Cache' },
    { value: 'sliding_window', label: 'Sliding Window' },
    { value: 'heavy_hitter',   label: 'Heavy Hitter' },
    { value: 'bdh_recurrent',  label: 'BDH Recurrent' },
  ];

  const isBudgetDisabled = cachePolicy === 'full';

  return (
    <div id="control-panel" aria-label="Simulation Controls">
      {/* ── Not yet implemented placeholder ── */}
      <div>ControlPanel — not yet implemented</div>

      {/*
        Day 2 implementation notes:
        - Policy selector: CONTROLS_SPEC §1.1  → POST /simulate { policy }
        - Budget slider:   CONTROLS_SPEC §1.2  → POST /simulate { budget }
          disabled (aria-disabled + pointer-events:none) when cachePolicy === "full"
        - Seq-length:      CONTROLS_SPEC §1.3  → POST /simulate { seq_len }
        - Needle count:    CONTROLS_SPEC §1.4  → POST /simulate { num_needles }
        All onChange calls should go through simulationStore.setField(name, value).
      */}
    </div>
  );
}

export default ControlPanel;
