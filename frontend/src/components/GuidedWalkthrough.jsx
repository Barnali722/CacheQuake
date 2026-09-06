/**
 * GuidedWalkthrough.jsx
 * Single responsibility: Manage and render the 5-step guided narrative flow
 * that walks the learner from the one-sentence claim through all four cache
 * policies before unlocking the sandbox, per PRD §4.3.
 *
 * Day 3: Steps 1–3 are state-driven — each step calls applyWalkthroughStep()
 * which simultaneously updates the control panel state AND runs a new simulation,
 * so the heatmap/readouts update as the narrative advances (not just the text).
 */

import React, { useEffect } from 'react';
import { useSimulation } from '../state/simulationStore';

// ─────────────────────────────────────────────────────────────────────────────
// Step definitions — each step drives specific control state + narration
// ─────────────────────────────────────────────────────────────────────────────

const STEPS = [
  {
    id: 1,
    title: 'The Claim — Watch Memory Grow',
    // State this step sets in the control panel:
    controlOverrides: {
      cachePolicy:    'full',
      sequenceLength: 128,
      budgetSize:     64,
      needleCount:    2,
    },
    narration: `
      Every time a Transformer generates a new token, it reads back over every token it has
      ever seen — and to avoid recomputing that work, it saves the keys and values from each
      attention head in a KV cache.
      With <strong>Full Cache</strong>, nothing is ever deleted. Every new token adds one row
      to the cache. Watch the memory chart: as sequence length grows, the cache grows with it
      — linearly, one step at a time. This is the cost of "perfect memory."
    `,
    hint: 'Drag the Sequence Length slider right and watch the memory chart climb.',
    highlightControl: 'sequenceLength',
  },
  {
    id: 2,
    title: 'Sliding Window — Simple Eviction, Clear Trade-off',
    controlOverrides: {
      cachePolicy:    'sliding_window',
      sequenceLength: 128,
      budgetSize:     64,
      needleCount:    2,
    },
    narration: `
      <strong>Sliding Window</strong> (StreamingLLM — Xiao et al., arXiv:2309.17453) caps memory by keeping only the
      most recent <em>budget</em> tokens. The cache stops growing once it reaches the budget —
      the memory chart plateaus while the full-cache baseline keeps climbing.
      But look at the heat-map: the tokens from the beginning of the sequence are gone.
      If one of the needle facts was buried early in the text, the model can no longer see it.
      Lower the budget and watch accuracy drop — that's the trade-off made explicit.
    `,
    hint: 'Lower the Budget slider and watch needles disappear from the heat-map.',
    highlightControl: 'budgetSize',
  },
  {
    id: 3,
    title: 'Heavy Hitter — Smarter Eviction, Different Failure Mode',
    controlOverrides: {
      cachePolicy:    'heavy_hitter',
      sequenceLength: 128,
      budgetSize:     64,
      needleCount:    2,
    },
    narration: `
      <strong>Heavy Hitter</strong> (H2O — Zhang et al., arXiv:2306.14048) evicts differently: instead of discarding the
      oldest tokens, it scores every token by how much cumulative attention it has received
      and keeps the top <em>budget</em> "heavy hitters."
      Tokens that were attended to often — including the needle facts — tend to survive.
      Compare the heat-map with Sliding Window: the alive cells are no longer a contiguous
      recent window; they are scattered wherever the model "cared" most.
      Accuracy at the same budget is often higher than Sliding Window — but the eviction
      pattern is harder to predict, and a needle buried in an unattended region can still be lost.
    `,
    hint: 'Switch back to Sliding Window at the same budget and compare the heat-map patterns.',
    highlightControl: 'cachePolicy',
  },
  {
    id: 4,
    title: 'BDH — Removing the Growth Entirely',
    controlOverrides: {
      cachePolicy:    'bdh_recurrent',
      sequenceLength: 128,
      budgetSize:     64,
      needleCount:    2,
    },
    narration: `
      <strong>Learning objective:</strong> Understand how BDH (Yıldız et al., arXiv:2509.26507)
      eliminates cache growth entirely by architectural design, not eviction.
      <br/><br/>
      <strong>BDH Recurrent</strong> takes a different architectural approach. Instead of
      appending to a growing list of keys and values, it maintains a <em>fixed-size state</em>
      that is overwritten by a local Hebbian update rule as each new token arrives.
      Memory never grows — it is O(1) regardless of sequence length. The memory chart is flat
      from the first token to the last.
      But this comes with a different failure mode: not eviction, but <em>interference</em>.
      New information overwrites old information in-place. The model can't "look back" at a
      specific earlier token — it can only recall what survived successive overwrites.
      <br/><br/>
      <strong>Note on BDH-CQ:</strong> The same paper introduces a BDH-CQ (contrastive-query)
      variant. Its relationship to standard KV cache eviction is indirect — this module teaches
      the core BDH memory model only, not BDH-CQ specifically.
    `,
    hint: 'Compare the BDH memory chart with Full Cache — flat vs. linear growth.',
    highlightControl: 'cachePolicy',
  },
  {
    id: 5,
    title: 'Trade-offs — The Full Picture',
    controlOverrides: null, // sandbox mode — no forced override
    narration: `
      You have now seen all four approaches:
      <br/><br/>
      • <strong>Full Cache</strong> — perfect memory, unbounded cost.
      <br/>
      • <strong>Sliding Window</strong> — bounded cost, loses early context predictably.
      <br/>
      • <strong>Heavy Hitter</strong> — bounded cost, keeps attended tokens, unpredictable gaps.
      <br/>
      • <strong>BDH Recurrent</strong> — O(1) memory, forgetting via interference, not eviction.
      <br/><br/>
      The sandbox below is now unlocked. Explore freely — change any control and see how each
      policy's heat-map, memory footprint, and retrieval accuracy respond.
    `,
    hint: null,
    highlightControl: null,
  },
];

// ─── Styles ──────────────────────────────────────────────────────────────────
const s = {
  banner: {
    background: '#1a1a28',
    borderBottom: '1px solid #2a2a44',
    padding: '10px 20px',
    display: 'flex',
    alignItems: 'flex-start',
    gap: '16px',
    flexWrap: 'wrap',
  },
  stepDots: {
    display: 'flex',
    gap: '6px',
    alignItems: 'center',
    paddingTop: '2px',
    flexShrink: 0,
  },
  dot: (state) => ({
    width: '24px',
    height: '24px',
    borderRadius: '50%',
    border: `2px solid ${state === 'done' ? '#3dffa0' : state === 'active' ? '#7b8cff' : '#333'}`,
    color: state === 'done' ? '#3dffa0' : state === 'active' ? '#7b8cff' : '#555',
    background: state === 'active' ? 'rgba(123,140,255,0.12)' : state === 'done' ? 'rgba(61,255,160,0.08)' : 'transparent',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: '10px',
    fontWeight: 600,
    flexShrink: 0,
    transition: 'all 0.2s ease',
  }),
  connector: (done) => ({
    width: '14px',
    height: '1px',
    background: done ? '#3dffa0' : '#2a2a3a',
    opacity: done ? 0.5 : 1,
    transition: 'background 0.3s',
  }),
  narrationBlock: {
    flex: 1,
    minWidth: '240px',
  },
  stepTitle: {
    fontSize: '12px',
    fontWeight: 700,
    color: '#c0c8ff',
    marginBottom: '4px',
  },
  narrationText: {
    fontSize: '12px',
    color: '#aaaacc',
    lineHeight: 1.6,
    maxHeight: '90px',
    overflowY: 'auto',
  },
  hint: {
    fontSize: '10px',
    color: '#7b8cff',
    marginTop: '4px',
    fontStyle: 'italic',
  },
  navButtons: {
    display: 'flex',
    gap: '6px',
    alignItems: 'center',
    flexShrink: 0,
    paddingTop: '2px',
  },
  btn: (primary, disabled) => ({
    border: `1px solid ${disabled ? '#333' : primary ? '#7b8cff' : '#444'}`,
    background: disabled ? '#0f0f14' : primary ? 'rgba(123,140,255,0.12)' : '#1e1e2e',
    color: disabled ? '#444' : primary ? '#7b8cff' : '#ccc',
    padding: '5px 14px',
    borderRadius: '4px',
    fontFamily: 'inherit',
    fontSize: '12px',
    cursor: disabled ? 'not-allowed' : 'pointer',
    transition: 'all 0.15s',
    whiteSpace: 'nowrap',
  }),
};

/**
 * GuidedWalkthrough
 *
 * Reads walkthroughStep from store via useSimulation().
 * On step advance: calls applyWalkthroughStep(controlOverrides) which:
 *   1. Updates control panel state (SET_CONTROLS_BATCH)
 *   2. Runs a new simulation → heatmap + charts update
 *
 * @see PRD_KV_Cache_Explainer.md §4.3
 * @see CONTROLS_SPEC.md §1.1–1.4
 */
function GuidedWalkthrough() {
  const { state, dispatch, applyWalkthroughStep } = useSimulation();
  const { walkthroughStep, sandboxUnlocked, isLoading } = state.ui;

  const stepIndex   = walkthroughStep - 1;
  const currentStep = STEPS[stepIndex] || STEPS[0];
  const isLastStep  = walkthroughStep === STEPS.length;

  // On mount and whenever walkthroughStep changes, apply the step's control overrides
  useEffect(() => {
    if (currentStep.controlOverrides) {
      applyWalkthroughStep(currentStep.controlOverrides);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [walkthroughStep]);

  const handleNext = () => {
    if (walkthroughStep < STEPS.length) {
      dispatch({ type: 'ADVANCE_WALKTHROUGH' });
    }
    if (walkthroughStep >= STEPS.length - 1) {
      dispatch({ type: 'UNLOCK_SANDBOX' });
    }
  };

  const handleBack = () => {
    if (walkthroughStep > 1) dispatch({ type: 'BACK_WALKTHROUGH' });
  };

  const handleSkip = () => {
    dispatch({ type: 'UNLOCK_SANDBOX' });
    dispatch({ type: 'SET_WALKTHROUGH_STEP', payload: 5 });
  };

  return (
    <div id="guided-walkthrough" style={s.banner} aria-label="Guided walkthrough navigation">

      {/* Step indicator dots */}
      <div style={s.stepDots} aria-label="Walkthrough progress">
        {STEPS.map((step, idx) => {
          const dotState =
            idx + 1 < walkthroughStep ? 'done' :
            idx + 1 === walkthroughStep ? 'active' : 'pending';
          return (
            <React.Fragment key={step.id}>
              {idx > 0 && <div style={s.connector(idx < walkthroughStep)} />}
              <div
                style={s.dot(dotState)}
                aria-label={`Step ${step.id}: ${step.title} — ${dotState}`}
                title={step.title}
              >
                {idx + 1 < walkthroughStep ? '✓' : step.id}
              </div>
            </React.Fragment>
          );
        })}
      </div>

      {/* Narration */}
      <div style={s.narrationBlock}>
        <div style={s.stepTitle}>
          Step {walkthroughStep}: {currentStep.title}
        </div>
        <div
          style={s.narrationText}
          dangerouslySetInnerHTML={{ __html: currentStep.narration.trim() }}
        />
        {currentStep.hint && (
          <div style={s.hint}>💡 {currentStep.hint}</div>
        )}
      </div>

      {/* Navigation */}
      <div style={s.navButtons}>
        <button
          onClick={handleBack}
          style={s.btn(false, walkthroughStep <= 1 || isLoading)}
          disabled={walkthroughStep <= 1 || isLoading}
          aria-label="Previous step"
        >
          ← Back
        </button>
        <button
          onClick={handleNext}
          style={s.btn(true, isLastStep || isLoading)}
          disabled={isLastStep || isLoading}
          aria-label={isLastStep ? 'Last step reached' : 'Next step'}
        >
          {isLoading ? '…' : isLastStep ? 'Done' : 'Next →'}
        </button>
        {!sandboxUnlocked && walkthroughStep < STEPS.length && (
          <button
            onClick={handleSkip}
            style={{ ...s.btn(false, false), opacity: 0.5, fontSize: '11px' }}
            aria-label="Skip to sandbox"
          >
            Skip to sandbox
          </button>
        )}
      </div>

    </div>
  );
}

export default GuidedWalkthrough;
