# Architecture — "Memory Under Pressure"
**Topic:** Key–Value Caching, Limitations, and Alternate Approaches · DataForge 2026 (Pathway x Rime)

---

## 1. High-level shape

```
Learner's browser
      │
      ▼
┌─────────────┐        HTTP/JSON        ┌─────────────┐
│  frontend/  │  ───────────────────►   │  backend/   │
│  (React UI) │  ◄───────────────────   │ (FastAPI +  │
└─────────────┘      step results       │ toy model)  │
                                          └─────────────┘
                                                │
                                                ▼
                                       precomputed data/
                                       (labeled, not live)
```

- **frontend/** owns everything the learner sees and touches: controls, guided walkthrough, cache heat-map, memory/accuracy readouts, sandbox mode, BDH module UI.
- **backend/** owns the actual computation: the toy Transformer, the four cache policies, the needle-in-haystack task generator, and an API that exposes cache state after every generation step (so the frontend is never faking behavior).
- **data/precomputed/** holds anything expensive we ran ahead of time (accuracy-vs-budget sweeps, the BDH-paper comparison numbers) — always clearly separated from the live path so we never blur "live" with "precomputed," which the rubric checks explicitly.

Why split this way: the "Interactive substrate & honesty" rubric item (15 pts) is checking exactly this — that the concept "truly behaves" and that live vs. precomputed is never conflated. Keeping backend = live compute and data/precomputed = everything else makes that distinction structural, not just a README note.

---

## 2. Folder structure

```
memory-under-pressure/
│
├── frontend/                      # Everything the learner interacts with
│   ├── public/
│   │   └── index.html
│   ├── src/
│   │   ├── components/
│   │   │   ├── ControlPanel.jsx           # policy / budget / seq-length controls
│   │   │   ├── CacheHeatmap.jsx           # which tokens are "alive" in cache
│   │   │   ├── MemoryChart.jsx            # live memory footprint vs. baseline
│   │   │   ├── AccuracyPanel.jsx          # retrieval accuracy vs. ground truth
│   │   │   ├── GuidedWalkthrough.jsx      # step 1→N narrative flow
│   │   │   ├── ComprehensionCheck.jsx     # inline check before "explain back"
│   │   │   ├── BDHModule.jsx              # dedicated BDH explainer step
│   │   │   ├── PrecomputedBadge.jsx       # reusable "published/precomputed" label
│   │   │   └── Sandbox.jsx                # free-play mode, all controls unlocked
│   │   ├── api/
│   │   │   └── client.js                  # thin wrapper around backend endpoints
│   │   ├── state/
│   │   │   └── simulationStore.js         # current policy/budget/seq state
│   │   ├── styles/
│   │   ├── App.jsx
│   │   └── index.jsx
│   └── package.json
│
├── backend/                       # All live computation — nothing here is faked
│   ├── app/
│   │   ├── main.py                        # FastAPI entrypoint
│   │   ├── model/
│   │   │   ├── toy_transformer.py         # tiny decoder-only model, forward pass
│   │   │   └── attention.py               # attention + KV cache instrumentation
│   │   ├── cache_policies/
│   │   │   ├── base.py                    # shared policy interface
│   │   │   ├── full_cache.py              # baseline, unbounded
│   │   │   ├── sliding_window.py          # StreamingLLM-style
│   │   │   ├── heavy_hitter.py            # H2O-style
│   │   │   └── bdh_inspired_state.py      # fixed-size recurrent, clearly labeled
│   │   ├── tasks/
│   │   │   └── needle_haystack.py         # synthetic sequence + needle generator
│   │   └── api/
│   │       ├── routes.py                  # /simulate, /step, /compare endpoints
│   │       └── schemas.py                 # request/response models
│   ├── precompute/
│   │   ├── generate_accuracy_curves.py    # runs the expensive budget sweeps once
│   │   └── generate_bdh_comparison.py     # packages BDH paper's published numbers
│   ├── tests/
│   └── requirements.txt
│
├── data/
│   └── precomputed/                # ONLY non-live data lives here, always labeled
│       ├── accuracy_vs_budget.json         # our own precomputed sweep results
│       └── bdh_published_claims.json       # BDH paper's numbers, source-cited, "not reproduced by us"
│
├── research/                      # Paper notes and primary-source grounding
│   ├── papers/
│   │   ├── h2o.md
│   │   ├── streamingllm.md
│   │   ├── snapkv.md
│   │   ├── quest.md
│   │   ├── kvzip.md
│   │   └── dragon_hatchling_bdh.md         # our primary BDH notes — quotes + page refs
│   └── citations.md                        # master citation list, used across README/blog/summary
│
├── docs/                          # Everything that gets submitted as text/PDF
│   ├── README.md                           # main project README (see §5 of PRD)
│   ├── one_page_summary.md  → .pdf         # 500–950 word standalone summary
│   ├── blog.md → .pdf                      # the "blog" deliverable
│   ├── LICENSES.md                         # source/license record for all reused assets
│   └── AI_DISCLOSURE.md                    # what was AI-assisted, logged honestly
│
├── assets/
│   ├── diagrams/                   # BDH synapse diagram, architecture diagrams, etc.
│   └── fonts/
│
├── .gitignore
├── LICENSE
└── ARCHITECTURE.md                 # this file
```

---

## 3. Data flow for one interaction (concrete walk-through)

1. Learner sets **policy = heavy-hitter**, **budget = 32**, **sequence length = 200** in `ControlPanel.jsx`.
2. `simulationStore.js` sends a request to `backend/app/api/routes.py` → `/simulate`.
3. `toy_transformer.py` runs the forward pass token-by-token; at each step, `heavy_hitter.py` decides which cache entries survive; `attention.py` returns the live cache state.
4. The API responds with, per step: memory footprint, which token indices are still cached, and (at the end) the model's answer to the needle question.
5. Frontend renders this into `CacheHeatmap.jsx` (live), `MemoryChart.jsx` (live vs. baseline), `AccuracyPanel.jsx` (model's answer vs. ground truth, fetched from the task generator, not invented).
6. If the learner instead asks to see the **budget sweep** (accuracy across many budgets, too expensive to run live), the frontend fetches from `data/precomputed/accuracy_vs_budget.json` — and `PrecomputedBadge.jsx` renders a visible "Precomputed" label wherever this data appears, per the honesty requirement.
7. The **BDH module** step (`BDHModule.jsx`) pulls its comparison numbers from `data/precomputed/bdh_published_claims.json`, sourced from `research/papers/dragon_hatchling_bdh.md`, always shown with a "Published claim, not reproduced by our team" badge.

---

## 4. Why this split is good for a 4-person team

- **Simulation/Backend engineer** owns `backend/` and `data/precomputed/` end to end — one clear boundary, no ambiguity about who touches the toy model.
- **Frontend/Interaction engineer** owns `frontend/` end to end, and only talks to the backend through the thin `api/client.js` contract — so backend internals can change without breaking the UI, and vice versa.
- **Research/Content lead** owns `research/` and drafts inside `docs/` (summary, blog) — their citation work directly feeds the `bdh_published_claims.json` and any in-UI citation text, so there's one source of truth (`research/citations.md`) instead of citations scattered across code and docs.
- **Docs/Design/Ops lead** owns final assembly of everything in `docs/` and `assets/`, plus repo hygiene (`.gitignore`, `LICENSE`, deployment) — they're the only one touching submission packaging, so nothing gets left out at the end.

The `data/precomputed/` folder being physically separate from `backend/app/` is deliberate: it makes it structurally obvious, even to a judge skimming the repo, which numbers are live-computed and which are shipped-as-data — directly supporting the "no hidden limits" and "truth beside estimate" design standards from the brief.

---

*Companion to `PRD_KV_Cache_Explainer.md`. Update this file if the stack or folder layout changes during the build.*
