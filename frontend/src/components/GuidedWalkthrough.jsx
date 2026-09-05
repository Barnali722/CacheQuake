/**
 * GuidedWalkthrough.jsx
 * Single responsibility: Manage and render the 5-step guided narrative flow
 * that walks the learner from the one-sentence claim through all four cache
 * policies before unlocking the sandbox, per PRD §4.3.
 */

import React from 'react';

/** Step definitions — content to be filled by Research/Content lead on Day 3 */
const STEPS = [
  {
    id: 1,
    title: 'Hook — Watch it grow',
    narration: '[Step 1 narration — placeholder. Content owner: Research/Content lead.]',
    focusControl: null, // No control focus on hook step
  },
  {
    id: 2,
    title: 'Full Cache — Linear growth',
    narration: '[Step 2 narration — placeholder.]',
    focusControl: 'sequenceLength',
  },
  {
    id: 3,
    title: 'Eviction — Trading exactness for budget',
    narration: '[Step 3 narration — placeholder.]',
    focusControl: 'cachePolicy',
  },
  {
    id: 4,
    title: 'BDH — Removing the growth entirely',
    narration: '[Step 4 narration — placeholder.]',
    focusControl: 'cachePolicy', // set to bdh_recurrent
  },
  {
    id: 5,
    title: 'Trade-off table — what each approach costs',
    narration: '[Step 5 narration — placeholder. Unlocked after ComprehensionCheck.]',
    focusControl: null,
  },
];

/**
 * GuidedWalkthrough
 *
 * Props:
 *   currentStep   {number}    1-based step index
 *   onNext        {function}  () => void — advance step
 *   onBack        {function}  () => void — go back one step
 *   onSkip        {function}  () => void — skip to sandbox (disabled until step 4)
 *
 * @see PRD_KV_Cache_Explainer.md §4.3
 */
function GuidedWalkthrough({
  currentStep = 1,
  onNext = () => {},
  onBack = () => {},
  onSkip = () => {},
}) {
  return (
    <div id="guided-walkthrough" aria-label="Guided walkthrough navigation">
      {/* ── Not yet implemented placeholder ── */}
      <div>GuidedWalkthrough — not yet implemented</div>

      {/*
        Day 2 implementation notes:
        - Render step dot indicators (1–5) with done/active/pending states.
        - Render narration text for STEPS[currentStep - 1].
        - Back / Next buttons; Next disabled on step 5 (sandbox instead).
        - "Skip to sandbox" enabled only after step 4 is reached.
        - ComprehensionCheck.jsx is injected inline before step 5 unlocks.
        - focusControl on each step should highlight the relevant control in ControlPanel.
      */}
    </div>
  );
}

export default GuidedWalkthrough;
