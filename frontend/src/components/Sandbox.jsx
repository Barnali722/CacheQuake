/**
 * Sandbox.jsx
 * Single responsibility: Render the free-play mode view where all four controls
 * (cachePolicy, budgetSize, sequenceLength, needleCount) are unlocked simultaneously,
 * without guided walkthrough constraints, per PRD §4.3.
 */

import React from 'react';

/**
 * Sandbox
 *
 * Props:
 *   isUnlocked   {boolean}   Whether sandbox mode has been unlocked (post-ComprehensionCheck)
 *   onLockClick  {function}  Called if learner clicks while locked (show hint to complete walkthrough)
 *
 * When unlocked, Sandbox renders the same ControlPanel + all readouts but with
 * no walkthrough narration or step constraints.
 *
 * @see PRD_KV_Cache_Explainer.md §4.3
 */
function Sandbox({ isUnlocked = false, onLockClick = () => {} }) {
  return (
    <div id="sandbox" aria-label="Sandbox — free-play mode">
      {/* ── Not yet implemented placeholder ── */}
      <div>Sandbox — not yet implemented</div>

      {/*
        Day 4 implementation notes:
        - When isUnlocked === false: render a locked overlay with hint text.
        - When isUnlocked === true: render ControlPanel + all readouts with no
          walkthrough constraints (all four controls enabled including budgetSize
          even for full cache — learner is free-exploring).
        - No narration text in this mode.
        - ComprehensionCheck.jsx is already passed at this point — do not re-render it here.
      */}
    </div>
  );
}

export default Sandbox;
