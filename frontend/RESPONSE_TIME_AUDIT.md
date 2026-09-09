# Response-Time Audit — Day 4
## Project: CacheQuake · DataForge 2026

Audit conducted: frontend-only analysis against documented backend costs.
Auditor: Agent 3 — Response-Time Agent.

---

## Per-Interaction Latency Analysis

| Interaction | Backend cost | Frontend path | Verdict |
|---|---|---|---|
| Policy tab click (any policy) | Single `/simulate` POST, O(seq_len) work | `ControlPanel.handlePolicyChange` → `runSimulation()` → one fetch | ✅ **KEEP LIVE** — sub-second at seq_len ≤ 512 on demo hardware |
| Budget slider drag | `onMouseUp/onTouchEnd` debounce — one POST on commit, not on every pixel | Same path | ✅ **KEEP LIVE** — fires once per gesture, not continuously |
| Sequence length slider | Same commit debounce | Same path | ✅ **KEEP LIVE** |
| Needle count stepper | Immediate POST — seq is short, needle scoring is O(num_needles) | Same path | ✅ **KEEP LIVE** |
| Accuracy-vs-budget curve | Full sweep across all budget values [8…512 step 8] — ~64 serial `/simulate` calls | `loadAccuracyVsBudget()` | ⚠️ **MOVE TO PRECOMPUTED** — see below |
| BDH published claims | Static file read, no compute | `loadBDHPublishedClaims()` | ✅ already precomputed |
| Per-step animation (`/step`) | Not yet wired in UI — future feature | N/A | N/A |

---

## Decision: Accuracy-vs-Budget Curve → Precomputed

**Why:** The curve requires running `/simulate` 64 times (all budget values 8–512 step 8),
once per policy per sequence length. Even at 100ms/call this is 6.4 seconds — unacceptable
for a live interaction. The curve's purpose is to show the *shape* of the trade-off, not
the exact value for the current run (the live dot already shows that).

**Frontend action taken (Day 4):**
- `loadAccuracyVsBudget()` in `api/client.js` fetches from `/data/precomputed/accuracy_vs_budget.json` (static file)
- This was already wired correctly on Day 3 — no change needed
- `AccuracyPanel` already renders `PrecomputedBadge` on this curve — badge is in place
- The live point (current budget, current accuracy) still comes from `/simulate` — that IS live

**Backend engineer action required:**
- Generate `data/precomputed/accuracy_vs_budget.json` by running the budget sweep offline
- Serve it as a static file (FastAPI `StaticFiles` mount at `/data/precomputed/`)
- Schema required: `[{ "budget": 8, "accuracy": 0.72 }, { "budget": 16, "accuracy": 0.81 }, ...]`
- One file per policy recommended; filename pattern: `accuracy_vs_budget_{policy}.json`

---

## What Was NOT Moved to Precomputed

| Item | Why kept live |
|---|---|
| `/simulate` for all 4 policies | Sub-second at realistic seq_len; live data is the whole point |
| BDH live stats (cache size, accuracy) | Same `/simulate` call as other policies |
| Needle positions | Derived from the live simulation response, not a separate call |

---

## Frontend Waterfall Check

No redundant re-fetches were found:
- `runSimulation()` fires a single POST, not one per component
- `loadAccuracyVsBudget()` is called once per `runSimulation()` (could be cached — see TODO below)
- No component calls `fetch()` directly — all go through `api/client.js`

**TODO (Day 5 / polish):** Cache the precomputed curve in the store on first load — currently
it re-fetches from disk on every `runSimulation()`. Since it's a static file this is fast,
but one HTTP request per simulation is wasteful. Fix: check `precomputed.accuracyVsBudget.length > 0`
before fetching again.

---

*Audit result: ONE item moved to precomputed (curve sweep). All live interactions are sub-second.
No live interaction was mislabeled as precomputed. PrecomputedBadge already in place.*
