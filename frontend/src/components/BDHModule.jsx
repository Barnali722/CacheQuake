/**
 * BDHModule.jsx
 * Single responsibility: Render the dedicated BDH explainer step — comparing
 * our toy simulator's bdh_recurrent results (live) against BDH paper published
 * claims (precomputed), with mandatory PrecomputedBadge, per CONTROLS_SPEC §2.5.
 */

import React from 'react';
import PrecomputedBadge from './PrecomputedBadge';

/**
 * BDHModule
 *
 * Props:
 *   liveStats         {object}  Our toy's stats for bdh_recurrent policy:
 *                               { cacheSizeTokens, accuracyScore } — from /simulate response
 *   publishedClaims   {object}  Loaded from data/precomputed/bdh_published_claims.json
 *                               Source: arXiv:2509.26507 — NOT reproduced by our team
 *
 * @see CONTROLS_SPEC.md §2.5
 * @see data/precomputed/bdh_published_claims.json
 * @see research/papers/dragon_hatchling_bdh.md
 */
function BDHModule({
  liveStats = null,
  publishedClaims = null,
}) {
  return (
    <div id="bdh-module" aria-label="BDH fixed-size recurrent state explainer">
      {/* ── Not yet implemented placeholder ── */}
      <div>BDHModule — not yet implemented</div>

      {/*
        Day 3 implementation notes:
        - Left column: our toy simulator stats (live /simulate response, bdh_recurrent policy).
          Label: "Our toy simulator" + LIVE badge.
        - Right column: BDH paper published claims (bdh_published_claims.json).
          MUST render PrecomputedBadge here with text:
          "Published result (arXiv:2509.26507) — not reproduced by our team"
        - Include disclaimer: "Our toy simulator ≠ the BDH model. Comparison is illustrative."
        - Diagram of BDH synaptic update mechanism to be added by Research/Content lead (Day 3).
        - This component only appears when cachePolicy === "bdh_recurrent" OR
          when GuidedWalkthrough.currentStep === 4.
      */}

      {/* PrecomputedBadge placeholder — mandatory on the published claims column */}
      <PrecomputedBadge text="Published result (arXiv:2509.26507) — not reproduced by our team" />
    </div>
  );
}

export default BDHModule;
