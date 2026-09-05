/**
 * AccuracyPanel.jsx
 * Single responsibility: Display needle retrieval accuracy — model_answers[] vs.
 * ground_truth_answers[] (live), plus the precomputed accuracy-vs-budget curve
 * with a PrecomputedBadge, per CONTROLS_SPEC §2.2 and §2.3.
 */

import React from 'react';
import PrecomputedBadge from './PrecomputedBadge';

/**
 * AccuracyPanel
 *
 * Props:
 *   modelAnswers        {string[]}  Model's answers — from /simulate { model_answers }
 *   correctAnswers      {string[]}  Ground-truth answers — from /simulate { ground_truth_answers }
 *   liveAccuracyScore   {number}    0–1 — from /simulate { accuracy_score }, live point on curve
 *   currentBudgetSize   {number}    Current budgetSize — for live dot placement on curve
 *   accuracyVsBudget    {object[]}  Precomputed sweep: [{ budget, accuracy }] from accuracy_vs_budget.json
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
  return (
    <div id="accuracy-panel" aria-label="Needle retrieval accuracy">
      {/* ── Not yet implemented placeholder ── */}
      <div>AccuracyPanel — not yet implemented</div>

      {/*
        Day 2 implementation notes:
        Section A — Needle table (CONTROLS_SPEC §2.2):
          - Column headers: "Needle", "Model output", "Correct answer"
          - Rows: one per needle; green if match, red if mismatch
          - Both modelAnswers and correctAnswers come from live /simulate response
          - No PrecomputedBadge on this section

        Section B — Accuracy-vs-budget curve (CONTROLS_SPEC §2.3):
          - Render precomputed curve (accuracyVsBudget) as an orange line
          - Overlay live point at (currentBudgetSize, liveAccuracyScore) as a blue dot
          - MUST render PrecomputedBadge beside the curve legend:
              text="Precomputed sweep — not this run"
          - Curve data loaded from data/precomputed/accuracy_vs_budget.json
      */}

      {/* PrecomputedBadge placeholder — will wrap the curve section */}
      <PrecomputedBadge text="Precomputed sweep — not this run" />
    </div>
  );
}

export default AccuracyPanel;
