/**
 * PrecomputedBadge.jsx
 * Single responsibility: Render a reusable, visually distinct label that marks
 * any data element as precomputed or published (not computed live this run),
 * satisfying the "honesty rubric" requirement from CONTROLS_SPEC §3.
 */

import React from 'react';

/**
 * PrecomputedBadge
 *
 * Renders a small inline badge with configurable text.
 * Use this component wherever CONTROLS_SPEC §3 specifies a PrecomputedBadge.
 *
 * Known placements (per CONTROLS_SPEC §3):
 *   1. AccuracyPanel — accuracy-vs-budget curve legend
 *      text="Precomputed sweep — not this run"
 *   2. BDHModule — published claims column
 *      text="Published result (arXiv:2509.26507) — not reproduced by our team"
 *
 * Props:
 *   text    {string}   Badge label text (required)
 *   style   {object}   Optional inline style overrides
 *
 * @see CONTROLS_SPEC.md §3
 */
function PrecomputedBadge({ text = 'Precomputed', style = {} }) {
  return (
    <span
      id="precomputed-badge"
      aria-label={`Data note: ${text}`}
      title={text}
      style={{
        display: 'inline-block',
        background: '#2d1f00',
        border: '1px solid #f5a623',
        color: '#f5a623',
        fontSize: '10px',
        padding: '2px 8px',
        borderRadius: '3px',
        marginLeft: '6px',
        verticalAlign: 'middle',
        ...style,
      }}
    >
      {text}
    </span>
  );
}

export default PrecomputedBadge;
