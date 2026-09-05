# wireframe_notes.md — "Memory Under Pressure"
**Agent 2 — Wireframe Agent · Day 1 · DataForge 2026**

---

## Overview

`wireframe.html` is a static, annotated low-fidelity wireframe of the "Memory Under Pressure"
interactive view. It requires no build step and no backend connection — open directly in a browser.
Every region carries an orange annotation bar referencing the corresponding entry in `CONTROLS_SPEC.md`.

---

## Screen Layout (3-column + 2 header rows)

```
┌──────────────────────────────────────────────────────────────────────┐
│ TOP BAR — title, one-sentence claim pill, track label                │
├──────────────────────────────────────────────────────────────────────┤
│ GUIDED WALKTHROUGH BANNER — step dots | narration text | nav buttons │
├─────────────────┬────────────────────────────┬───────────────────────┤
│ LEFT COLUMN     │ CENTER COLUMN              │ RIGHT COLUMN          │
│ ControlPanel    │ CacheHeatmap (top ~40%)    │ AccuracyPanel (top)   │
│ .jsx            │                            │                       │
│                 │ MemoryChart  (bottom ~60%) │ BDHModule (bottom)    │
├──────────────────┴────────────────────────────┴───────────────────────┤
│ FOOTER — static label + file links                                    │
└───────────────────────────────────────────────────────────────────────┘
```

Breakpoint note: the 3-column grid collapses to a single column on screens < 900px wide.
The mobile layout stacks: Walkthrough → Controls → Heatmap → Chart → Accuracy → BDH.

---

## Region-by-Region Notes

### 1. Top Bar
- Title: "Memory Under Pressure"
- One-sentence claim shown as a pill — this is the framing statement the whole
  artifact teaches. Learner sees it before any interaction.
- No CONTROLS_SPEC entry (static display only).

### 2. GuidedWalkthrough.jsx Banner
- 5 step-dots: step 1 = done (green), step 2 = active (purple), steps 3–5 = inactive.
- Narration text is the scripted explanation for the active step.
- Back / Next navigation. "Skip to sandbox" link shows but greys until step 4.
- CONTROLS_SPEC reference: indirectly maps to all controls (each step unlocks or focuses
  one control in sequence).
- ComprehensionCheck.jsx activates **between step 4 and step 5** (inline, below the
  narration text — not shown in this wireframe). It gates the sandbox unlock.

### 3. ControlPanel.jsx (left column)
| Sub-region | CONTROLS_SPEC ref |
|---|---|
| Cache Policy (segmented 4-tab) | §1.1 — `cachePolicy` |
| Budget Size slider | §1.2 — `budgetSize` (disabled/greyed when policy="full") |
| Sequence Length slider | §1.3 — `sequenceLength` |
| Needle Count stepper | §1.4 — `needleCount` |
| Sandbox.jsx (collapsed) | §1.1–1.4 all unlocked, no walkthrough override |

- The wireframe shows Budget Size greyed out because the active policy is "Full Cache."
- Sandbox.jsx appears as a collapsed toggle at the bottom of the control panel;
  it expands to the same control set but without walkthrough constraints.

### 4. CacheHeatmap.jsx (center, top)
- **Two rows of cells:** current policy (top) vs. Full Cache baseline (bottom).
- Red cells = needle token positions (same in both rows — they're in the sequence regardless).
- Green = alive in cache. Dark grey = evicted.
- **LIVE badge** — `alive_token_indices[]` comes from `/simulate` response (CONTROLS_SPEC §2.4).
- No PrecomputedBadge here.

### 5. MemoryChart.jsx (center, bottom)
- Two-line chart: live policy (blue/purple line) vs. full-cache baseline (dashed grey).
- X-axis = generation step. Y-axis = tokens in cache.
- **LIVE badge** — both lines from `/simulate` response (CONTROLS_SPEC §2.1).
- No PrecomputedBadge here.
- The divergence between the two lines is the primary visual payoff of the linear-growth claim.

### 6. AccuracyPanel.jsx (right, top)
| Sub-region | CONTROLS_SPEC ref |
|---|---|
| Needle table (Model output vs. Correct answer) | §2.2 — `model_answers[]` vs. `ground_truth_answers[]` |
| Accuracy-vs-budget curve (orange) | §2.3 — `accuracy_vs_budget.json` (precomputed) |
| Live point on curve (blue dot) | §2.3 — `accuracy_score` from live `/simulate` |

- **PRECOMPUTED badge** on the curve (not the dot) — text:
  "Precomputed sweep — not this run"
  (CONTROLS_SPEC §3, PrecomputedBadge.jsx placement #1)

### 7. BDHModule.jsx (right, bottom)
| Sub-region | CONTROLS_SPEC ref |
|---|---|
| Left column: "Our toy simulator" stats | §2.5 — live `/simulate` response, bdh_recurrent policy |
| Right column: "BDH paper claims" | §2.5 — `bdh_published_claims.json` (precomputed, published) |

- **LIVE badge** on left column.
- **PUBLISHED / PRECOMPUTED badge** on right column — text:
  "Published result (arXiv:2509.26507) — not reproduced by our team"
  (CONTROLS_SPEC §3, PrecomputedBadge.jsx placement #2)
- Disclaimer text under the comparison: "Our toy simulator ≠ the BDH model."

---

## PrecomputedBadge Placements (summary)

| # | Location in wireframe | Badge text |
|---|---|---|
| 1 | AccuracyPanel — accuracy-vs-budget curve legend | "Precomputed sweep — not this run" |
| 2 | BDHModule — right/published column header | "Published result (arXiv:2509.26507) — not reproduced by our team" |

Both placements use `PrecomputedBadge.jsx` (CONTROLS_SPEC §3).

---

## What Is NOT in the Wireframe (Day 2+ scope)
- Real chart rendering (Chart.js / D3) — placeholder SVG lines only
- Live API calls — no fetch() anywhere
- Real heatmap data — cells are randomly seeded for visual layout only
- ComprehensionCheck.jsx questions — gated for Day 2 content
- Mobile responsive breakpoints — noted in layout but not wired

---

## Files This Wireframe Was Validated Against
- `CONTROLS_SPEC.md` (Agent 1 output) — every annotation checked
- `ARCHITECTURE.md §3` — data flow confirmed (no invented data sources)
- `PRD_KV_Cache_Explainer.md §4.3` — guided path + sandbox flow matches §4.3 exactly

---

*Produced by Agent 2 — Wireframe Agent.*
*Reviewed by Agent 4 — Reviewer Agent. Companion: `CONTROLS_SPEC.md`, `wireframe.html`.*
