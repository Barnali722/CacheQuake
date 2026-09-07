/**
 * ComprehensionCheck.jsx
 * Single responsibility: Gate the sandbox unlock with a 2-question inline
 * comprehension check before the learner reaches the free-play step,
 * per PRD §4.3 ("Checkpoint").
 */

import React from 'react';

/**
 * Questions are intentionally unset here — content owner is Research/Content lead.
 * Answers must reference the live simulation state (e.g., "what happens if you
 * evict the needle token?") — no precomputed answers, no trivia.
 */
const QUESTIONS = [
  {
    id: 'q1',
    prompt: '[Question 1 — placeholder. Content owner: Research/Content lead.]',
    options: ['[Option A]', '[Option B]', '[Option C]'],
    correctIndex: 0, // to be set on Day 3
  },
  {
    id: 'q2',
    prompt: '[Question 2 — placeholder.]',
    options: ['[Option A]', '[Option B]', '[Option C]'],
    correctIndex: 1,
  },
];

/**
 * ComprehensionCheck
 *
 * Props:
 *   onPass   {function}  () => void — called when learner answers both correctly
 *   onRetry  {function}  () => void — called on incorrect answer (no penalty, just reset)
 *
 * @see PRD_KV_Cache_Explainer.md §4.3
 */
function ComprehensionCheck({
  onPass = () => {},
  onRetry = () => {},
}) {
  return (
    <div id="comprehension-check" aria-label="Comprehension check — required before sandbox">
      {/* ── Not yet implemented placeholder ── */}
      <div>ComprehensionCheck — not yet implemented</div>

      {/*
        Day 3 implementation notes:
        - Render QUESTIONS one at a time (or both at once — UX TBD with Docs/Design lead).
        - On both correct: call onPass() → GuidedWalkthrough advances to step 5, sandbox unlocks.
        - On incorrect: show explanation, allow retry with no penalty.
        - Questions should NOT have correct answers hardcoded visibly in the DOM.
      */}
    </div>
  );
}

export default ComprehensionCheck;
