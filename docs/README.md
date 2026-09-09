# CacheQuake — Memory Under Pressure

**An interactive explainer on why a Transformer's KV cache grows without bound, what eviction and compression trade away to control it, and how a fixed-size associative state (inspired by BDH) offers a different way out entirely.**

Built for **DataForge 2026** (Pathway × Rime track) · Topic: *Key–Value Caching, Limitations, and Alternate Approaches*.

> ⚠️ **Repository note:** several planning documents in this repo (`ARCHITECTURE (1).md`, `PRD_KV_Cache_Explainer.md`, `backend/README.md`) describe the *intended* Day-1 design, including a `research/` folder of paper notes and a `backend/app/api/routes.py` split. **Neither exists in the actual codebase.** This file documents what is actually implemented and call out every place the plan and the code diverge. The root [`README.md`](../README.md) is now the primary, most current entry point — see its [§21 "Known documentation vs. implementation drift"](../README.md#21-known-documentation-vs-implementation-drift) for the fullest reconciled list, including two issues (a stale `LICENSES.md` claim and a fabricated figure in the frontend's offline demo fallback) found after this file was written. See [Limitations](#limitations--honest-scope) below for this file's own list.

---

## 1. The problem, in one sentence

> A Transformer's KV cache grows linearly with every token it has ever seen because it stores an exact copy of the past; eviction and compression trade that exactness for a bounded budget, and architectures like BDH remove the growth altogether by replacing the cache with a fixed-size associative state that overwrites itself instead of appending.

During autoregressive generation, a Transformer stores the Key and Value projections it has already computed so it never has to recompute them for earlier tokens. That cache is what makes generation fast — and it's also what makes long contexts expensive. Roughly:

```
KV memory  ∝  sequence length × layers × KV heads × head dimension × bytes per element
```

(This is a conceptual relationship for building intuition, not a formula CacheQuake reproduces exactly for a specific production model — see [§5](#5-what-the-backend-actually-computes).)

## 2. What CacheQuake teaches

Nine sequential ideas, each testable in the live simulator:

1. Why decoding needs a KV cache at all.
2. Why that cache's size scales with sequence length, layers, heads, and head dimension.
3. What happens under memory pressure — something has to be evicted, compressed, or restructured.
4. What a **sliding-window** policy keeps and discards, and where it fails.
5. What a **heavy-hitter** (attention-score-based) policy keeps and discards, and where it wins.
6. How a **fixed-size associative state** (toy layer inspired by BDH) sidesteps eviction entirely — and what it gives up instead (interference, not eviction).
7. How these strategies trade off memory vs. retrieval accuracy on a controlled needle-in-a-haystack task.
8. Why "live" and "precomputed" numbers must never be blurred together.
9. Why none of this is a claim that a toy simulator reproduces a frontier model.

## 3. Solution: an interactive needle-in-a-haystack simulator

CacheQuake runs a small, real, from-scratch decoder-only Transformer and lets the learner choose a cache policy, then watch — token by token — which past positions stay visible in the cache and whether the model can still answer a question about a fact buried earlier in the sequence.

```
Context Length → KV Cache → Memory Pressure → Retention / Eviction → Information Availability → Retrieval Quality
```

**Why this matters:** every deployed LLM chat product a learner has used hits this exact bottleneck. Understanding it is the shortest path from "I've used a chatbot" to "I understand a live architectural debate" (BDH included).

## 4. Key features

- A real PyTorch Transformer (4 layers, d_model=64, 4 heads, character-level vocab) — no HuggingFace wrapper, every line inspectable.
- Four interchangeable cache policies behind one shared interface (`CachePolicy`).
- A synthetic needle-in-a-haystack task generator with reproducible seeds.
- A `/simulate` endpoint that returns the full per-token cache trace so the frontend never fakes behavior.
- A guided, five-step walkthrough plus an unlockable sandbox with all controls exposed.
- Every number in the UI is labeled **LIVE**, **PRECOMPUTED — OUR RESULT**, or **PUBLISHED RESULT — NOT REPRODUCED** (see [§6](#6-scientific-honesty--provenance)).

## 5. What the backend actually computes

| Component | File | Status |
|---|---|---|
| Toy Transformer (attention, embeddings, forward pass) | `backend/app/model/` | ✅ Implemented, real forward pass |
| Full cache (baseline, keep everything) | `backend/app/cache_policies/full_cache.py` | ✅ Implemented |
| Sliding window + attention sinks (StreamingLLM-inspired) | `backend/app/cache_policies/sliding_window.py` | ✅ Implemented |
| Heavy-hitter eviction (H2O-inspired, proxy dot-product score) | `backend/app/cache_policies/heavy_hitter.py` | ✅ Implemented |
| BDH-inspired fixed-size state (**not** a BDH reproduction) | `backend/app/cache_policies/bdh_inspired_state.py` | ✅ Implemented |
| Needle-in-a-haystack task generator | `backend/app/tasks/needle_haystack.py` | ✅ Implemented |
| Token-by-token simulation runner | `backend/app/simulation/runner.py` | ✅ Implemented |
| `GET /health`, `POST /simulate` | `backend/app/main.py` | ✅ Implemented (all in `main.py`, not a separate `routes.py`) |
| `POST /step` (single-step streaming) | `backend/app/main.py` | 🔲 Stub — returns HTTP 501 |
| Comprehension-check questions | `frontend/src/components/ComprehensionCheck.jsx` | 🔲 Placeholder text, not authored yet — `[VERIFY IMPLEMENTATION]` |

## 6. Cache policies at a glance

| Policy | File | Memory | Retention rule | Educational question |
|---|---|---|---|---|
| Full Cache | `full_cache.py` | Grows with context, one row/token/layer | None — nothing is ever evicted | What if memory were unlimited? |
| Sliding Window | `sliding_window.py` | Bounded: `num_sink_tokens + window_size` | Keep first *S* "sink" tokens + last *W* recent tokens | What happens when old context is removed? *Inspired by StreamingLLM (Xiao et al., 2023); not an exact reproduction.* |
| Heavy Hitter | `heavy_hitter.py` | Bounded: fixed `budget` | Keep the tokens with highest cumulative proxy attention score, always keep the most recent | Can selective retention beat a full cache? *Inspired by H2O (Zhang et al., 2023); uses a documented dot-product proxy score, not the paper's softmax weights.* |
| BDH-Inspired State | `bdh_inspired_state.py` | **Constant**: `state_size`, independent of sequence length | Overwrite a fixed slot array via a soft, decayed, similarity-weighted write | Can memory be represented differently from an explicit token history? |

> **BDH disclaimer (read this before trusting the fourth row):** `bdh_inspired_state.py` is a **toy layer inspired by BDH, not BDH itself**. It borrows the conceptual idea of a fixed-size, overwriting associative state from *"The Dragon Hatchling: The Missing Link between the Transformer and Models of the Brain"* (Kosowski, Uznański, Chorowski, Stamirowska, Bartoszkiewicz; arXiv:2509.26507, Pathway). It does **not** reproduce BDH's scale-free neuron-particle graph, spiking dynamics, or learned synaptic update rules — the write rule here is a hand-designed EMA + softmax-addressing update. See `backend/app/cache_policies/bdh_inspired_state.py` for the full, itemized list of simplifications, and `backend/data/precomputed/bdh_published_claims.json` for exactly which BDH claims are cited and how.

## 7. Architecture overview

```
Learner's browser
      │
      ▼
frontend/ (React + Vite)  ──HTTP/JSON──►  backend/ (FastAPI + PyTorch, CPU-only)
      ▲                                          │
      │                                          ▼
      └── data/precomputed/*.json ◄── labeled, non-live results
```

Full detail, including the concrete data flow for one interaction and where the planned layout differs from the shipped code, is in [`ARCHITECTURE.md`](ARCHITECTURE.md).

## 8. Tech stack

- **Frontend:** React 18, Vite 5, plain CSS-in-JS, no TypeScript. Deployed as a static site via GitHub Actions → GitHub Pages.
- **Backend:** FastAPI 0.115, PyTorch ≥2.3 (CPU-only), Pydantic 2, pytest. Deployed to Hugging Face Spaces.
- Full dependency list and rationale: [`TECH_STACK.md`](TECH_STACK.md).

## 9. Quick start

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
# → GET http://localhost:8000/health

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

Full setup, troubleshooting, and how to reproduce the precomputed data from scratch: [`backend/SETUP.md`](backend/SETUP.md).

## 10. Repository structure

```
CacheQuake-main/
├── README.md                    # this file
├── ARCHITECTURE.md              # actual system architecture + plan-vs-reality notes
├── TECH_STACK.md                # dependency list and deployment notes
├── PRD_KV_Cache_Explainer.md    # original product requirements doc (Day 0 planning)
├── docs/
│   ├── README.md                 # full project documentation
│   ├── one_page_summary.md       # ~700-word standalone summary
│   ├── blog.md                   # blog-style writeup
│   ├── LICENSES.md               # dependency & asset license record
│   └── AI_DISCLOSURE.md          # AI-assistance disclosure
├── research/
│   └── citations.md              # master reference list
├── backend/
│   ├── app/
│   │   ├── main.py                # FastAPI app — /health, /simulate, /step (501)
│   │   ├── model/                 # ToyTransformer, attention, vocab
│   │   ├── cache_policies/        # full_cache, sliding_window, heavy_hitter, bdh_inspired_state
│   │   ├── simulation/            # runner.py — token-by-token episode loop
│   │   └── tasks/                 # needle_haystack.py
│   ├── scripts/                   # train_toy.py, generate_accuracy_sweep.py, perf tools
│   ├── data/precomputed/          # accuracy_vs_budget.json, bdh_published_claims.json
│   ├── model_weights/             # toy_transformer.pt + training_metadata.json
│   └── tests/                     # 72 pytest tests (smoke, Day 2, Day 3)
└── frontend/
    └── src/
        ├── components/            # ControlPanel, CacheHeatmap, MemoryChart, AccuracyPanel,
        │                          # GuidedWalkthrough, ComprehensionCheck, BDHModule,
        │                          # PrecomputedBadge, Sandbox, ErrorBoundary
        ├── api/client.js           # thin fetch wrapper — never falls back to mocks
        └── state/simulationStore.jsx
```

## 11. Research foundations

Primary sources cited across this documentation and the UI (full list with abstracts and verification notes in [`research/citations.md`](research/citations.md)):

- Vaswani et al., *Attention Is All You Need*, arXiv:1706.03762 (2017)
- Xiao et al., *Efficient Streaming Language Models with Attention Sinks* (StreamingLLM), arXiv:2309.17453 (2023, ICLR 2024)
- Zhang et al., *H2O: Heavy-Hitter Oracle for Efficient Generative Inference of LLMs*, arXiv:2306.14048 (NeurIPS 2023)
- Li et al., *SnapKV: LLM Knows What You Are Looking For Before Generation*, NeurIPS 2024 — cited, not simulated
- Tang et al., *Quest: Query-Aware Sparsity for Efficient Long-Context LLM Inference*, arXiv:2406.10774 (2024) — cited, not simulated
- Kim et al., *KVzip: Query-Agnostic KV Cache Compression with Context Reconstruction*, arXiv:2505.23416 (2025) — cited, not simulated
- Kosowski, Uznański, Chorowski, Stamirowska, Bartoszkiewicz, *The Dragon Hatchling: The Missing Link between the Transformer and Models of the Brain* (BDH), arXiv:2509.26507 (Pathway, 2025)

> A no-longer-current planning note: `docs/one_page_summary.md` (Day 0 draft) refers to BDH by an earlier working title ("Beyond Dense-Hop") and attributes it to "Yıldız et al." Neither matches the published paper. The correct title is *The Dragon Hatchling*, and the correct authors are Kosowski, Uznański, Chorowski, Stamirowska, and Bartoszkiewicz (Pathway). This README and `research/citations.md` use the verified citation; `docs/one_page_summary.md` should be corrected before final submission.

## 12. Scientific honesty / provenance

Every number in CacheQuake belongs to exactly one of these categories, and the UI labels it accordingly:

| Label | Meaning |
|---|---|
| **LIVE SIMULATION** | Computed by the backend, right now, in response to the learner's `/simulate` request. |
| **PRECOMPUTED — OUR RESULT** | Generated by CacheQuake's own scripts (`backend/scripts/generate_accuracy_sweep.py`) and stored in `backend/data/precomputed/accuracy_vs_budget.json`. |
| **PUBLISHED RESULT — NOT REPRODUCED** | Taken from an external paper (currently only BDH), stored in `backend/data/precomputed/bdh_published_claims.json`, never presented as something CacheQuake measured. |
| **EDUCATIONAL INTERPRETATION** | An explanation authored by the team to build intuition, not a measurement. |

Full detail, including the exact locked accuracy table, is in [`backend/README.md`](../backend/README.md#locked-accuracy-numbers-80-episodes-eval-seed-base100-v3-checkpoint) and in the root [`README.md` §9](../README.md#9-accuracy-vs-budget).

## 13. Limitations / honest scope

- The model is a **4-layer, d_model=64 toy Transformer**, lightly trained (5,000 steps) on its own synthetic task — not a pretrained LLM and not benchmark-evaluated. See `backend/model_weights/training_metadata.json`.
- The needle-in-a-haystack task is synthetic and character-level; it demonstrates the cache/retention mechanism structurally, not real-world long-context reasoning.
- `heavy_hitter.py` uses a documented **proxy** dot-product score, not the softmax attention weights H2O's paper uses to rank tokens — this is explained in the file's own docstring.
- `bdh_inspired_state.py` is an **educational abstraction inspired by BDH**, not a reproduction of BDH's architecture, training procedure, or benchmark results. Its published-claims comparison file (`bdh_published_claims.json`) intentionally ships an **empty** `quantitative_claims` list rather than a guessed number, because the team did not have verified access to BDH's exact benchmark table entries at submission time.
- `POST /step` (single-token streaming) is not implemented — it returns HTTP 501.
- `frontend/src/components/ComprehensionCheck.jsx` ships with placeholder question text; content was not authored before submission.
- Precomputed sweep numbers (`accuracy_vs_budget.json`) reflect one fixed experimental configuration (80 episodes, `n_facts=3`, `seq_len=120`, one eval seed base) and should not be read as a general benchmark.
- Several planning documents (`ARCHITECTURE (1).md`, `PRD_KV_Cache_Explainer.md`, `backend/README.md`) describe a `research/papers/` folder and a `backend/app/api/routes.py` / `schemas.py` split that were **not** built — see the root [`README.md` §21](../README.md#21-known-documentation-vs-implementation-drift) for the fullest reconciled list.

## 14. AI disclosure

AI assistance was used during development and documentation. The team remained responsible for implementation, verification, testing, and final decisions. Full disclosure: [`docs/AI_DISCLOSURE.md`](docs/AI_DISCLOSURE.md).

## 15. License

See [`docs/LICENSES.md`](docs/LICENSES.md) for a per-dependency and per-asset breakdown. **No repository-wide LICENSE file was found in this codebase at the time this documentation was written** — `[VERIFY LICENSE]`. The team should add one before public release if the project is meant to be open source.

## 16. Team

**Team Game of Codes** — DataForge 2026

- Barnali Tanti — Team Leader
- Sangramjeet Choudhury
- MD Aftab Hossain
- Jayita Jana

Per-member contributions to specific files/components are not recorded anywhere in the repository at the time of writing — `[VERIFY CONTRIBUTIONS]`.

## 17. Further reading

- [`ARCHITECTURE.md`](ARCHITECTURE.md) — full system architecture, actual vs. planned
- [`README.md`](../README.md) — primary judge-facing entry point (all 27 sections, including the reconciled drift list)
- [`docs/one_page_summary.md`](docs/one_page_summary.md) — standalone ~700-word summary
- [`docs/blog.md`](docs/blog.md) — blog-style writeup
- [`research/citations.md`](research/citations.md) — full reference list
- [`backend/README.md`](backend/README.md) / [`backend/SETUP.md`](backend/SETUP.md) — backend API contract and setup
