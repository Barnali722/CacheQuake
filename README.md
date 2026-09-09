<<<<<<< HEAD
# CacheQuake

**CacheQuake** is an interactive explainer on why LLMs' KV cache grows without bound, what eviction and compression trade away, and how Pathway's BDH replaces the cache with a fixed-size synaptic state instead. Built for the DataForge 2026 IITKGP Hackathon (Pathway x Rime track).

## 1. The Claim

A Transformer's KV cache grows linearly with every token it has ever seen because it stores an exact copy of the past. Eviction and compression trade that exactness for a bounded budget. Architectures like BDH remove the growth altogether by replacing the cache with a fixed-size associative state that overwrites itself instead of appending.

## 2. Audience

ML practitioners, students, and technically curious non-experts who have heard of "attention" but have not thought carefully about inference-time memory costs.

## 3. Learning Objectives

By the end of the interactive walkthrough, users will be able to:
1. Explain *why* the KV cache grows linearly.
2. Describe *what each eviction policy trades away* — early context (Sliding Window / StreamingLLM) vs. unattended tokens (Heavy Hitter / H2O).
3. Explain *how BDH removes the growth* — fixed-size matrix, Hebbian overwrite, interference instead of eviction.
4. Predict *what happens to needle retrieval accuracy* as the budget shrinks for each policy.

## 4. Architecture

CacheQuake consists of:
- **Backend (FastAPI & PyTorch)**: A custom 4-layer, character-level decoder-only toy Transformer. It serves a `/simulate` endpoint to run live inference forward passes with specific cache policies.
- **Frontend (React & Vite)**: An interactive UI that visualizes cache state, memory growth, and retrieval accuracy in real-time.

### Live vs. Precomputed
- **Live**: All heatmap states, memory charts, and step-by-step token tracking are generated via live inference calls to the backend API (`/simulate`). 
- **Precomputed**: The accuracy vs. budget sweeps and BDH published accuracy claims are precomputed or static to save compute time and avoid reproducing massive model training runs. They are marked with a distinct "Precomputed" badge in the UI.

## 5. Reproduction Steps

### Backend
1. `cd backend`
2. `python -m venv .venv`
3. Activate the environment (e.g., `.\.venv\Scripts\activate`)
4. `pip install -r requirements.txt`
5. `uvicorn app.main:app --reload` (Runs on `localhost:8000`)

### Frontend
1. `cd frontend`
2. `npm install`
3. `npm run dev` (Runs on `localhost:5173`)

## 6. Citations & References

This explainer builds upon the concepts presented in the following primary papers:
1. **StreamingLLM**: Xiao et al., "Efficient Streaming Language Models with Attention Sinks" (2023) — [arXiv:2309.17453](https://arxiv.org/abs/2309.17453)
2. **H2O**: Zhang et al., "H2O: Heavy-Hitter Oracle for Efficient Generative Inference of Large Language Models" (2023) — [arXiv:2306.14048](https://arxiv.org/abs/2306.14048)
3. **BDH**: Yıldız et al., "Beyond Dense-Hop" (2025) — [arXiv:2509.26507](https://arxiv.org/abs/2509.26507)
4. Vaswani et al., "Attention Is All You Need" (2017) — [arXiv:1706.03762](https://arxiv.org/abs/1706.03762)

## 7. Credits & License

Distributed under the MIT License. See `LICENSE` for more information.
Created for DataForge 2026.

## 8. AI-Assistance Disclosure

This project was developed with the assistance of an AI coding assistant (Google Gemini / Antigravity). The AI assisted in writing UI boilerplate, scaffolding the FastAPI backend structure, and generating documentation templates. All core architecture decisions, cache policy logic implementations, and educational narratives were guided and verified by the authors.
=======
# ⚡ CacheQuake
### Making KV-Cache Memory Visible

**DataForge 2026 · Pathway × Rime · Explain the Frontier**

**Topic:** Key–Value (KV) Caching, Its Limitations, and Alternative Memory Approaches
**Team:** Game of Codes

| Member | Role |
|---|---|
| Barnali Tanti | Team Leader |
| Sangramjeet Choudhury | Member |
| MD Aftab Hossain | Member |
| Jayita Jana | Member |

---

## Project Claim

KV caching reduces redundant Key–Value computation during autoregressive LLM generation, but its memory requirements grow with context length — motivating both more memory-efficient KV-cache management **and** alternative memory mechanisms such as BDH (Dragon Hatchling).

## Audience

This project is for students, developers, and learners who want to understand how KV caching affects LLM inference, and how different approaches — from cache eviction heuristics to a fundamentally different architecture — try to reduce or rethink its memory cost.

## Objectives

1. Explain the role of KV caching in autoregressive LLM generation.
2. Demonstrate why KV-cache memory grows with context length.
3. Compare different KV-cache management strategies side by side.
4. Introduce BDH / BDH-GPU as an alternative, architecture-level memory approach.
5. Provide an interactive visualization that makes these trade-offs easy to see and compare.

---

## 1. The Problem

Transformer-based LLMs cache the Key and Value states of every previous token during autoregressive generation, so they don't have to recompute them at each new step. This makes generation efficient — but the cache grows linearly with context length and batch size, and for long-context models (128K–1M+ tokens) it becomes the dominant memory and latency bottleneck. Loading a large KV cache during self-attention can consume over half of total inference time at long context lengths.

## 2. Why KV-Cache Management Matters

Since storing every token's KV pair becomes expensive at scale, researchers have explored two broad directions:

- **Cache management** — keep the Transformer architecture as-is, but be smarter about *which* KV pairs are retained, evicted, or loaded.
- **Architecture-level alternatives** — rethink how the model represents memory in the first place, rather than patching the cache.

CacheQuake covers both directions, using five KV-cache papers for the first and one architecture paper (BDH) for the second.

## 3. Approaches Covered

| Method | Type | Core Mechanism |
|---|---|---|
| **Full Cache** | Baseline | Retains every token's KV pair — no compression. |
| **Sliding Window** | Baseline | Retains only the most recent *N* tokens. |
| **H2O** (Heavy-Hitter Oracle) | Dynamic eviction | Greedy, per-step retention of "Heavy-Hitter" + recent tokens via dynamic submodular optimization. |
| **SnapKV** | Prefill-time selection | One-shot, voting-based selection of important KV positions from an end-of-prompt "observation window." |
| **StreamingLLM** | Structural / fixed | Retains fixed initial "attention sink" tokens + a sliding recent window; no retraining required. |
| **Quest** | Query-aware sparsity | Page-level Min/Max-Key criticality scoring against the live Query vector; sparsifies which pages are *loaded*, not what's stored. |
| **KVzip** | Query-agnostic compression | Reconstruction-based importance scoring so one compressed cache can be reused across many different queries. |
| **BDH / BDH-GPU** | Architecture-level alternative | Scale-free, biologically-inspired local graph dynamics with Hebbian/spiking working memory — not a KV-cache method at all. |

Detailed notes for each paper — core idea, problem, method, key results, limitations, and how it relates to the others — live in `research/papers/`.

## 4. What Our Project Explores

CacheQuake provides an **interactive comparison** of different strategies for handling the memory cost of long-context LLM inference:

- It runs Full Cache, Sliding Window, H2O, SnapKV, and StreamingLLM through our own simulation pipeline and visualizes accuracy vs. KV-cache budget.
- It separately presents BDH/BDH-GPU as an architecture-level alternative, using **published** figures from the original paper rather than results we generated ourselves.
- Quest and KVzip are included as further reading / comparison points in the research notes, representing the two newer directions (query-aware loading vs. query-agnostic compression) that extend beyond the three "classic" eviction methods.

## 5. Key Takeaway

KV caching avoids redundant computation during autoregressive generation, but its memory cost grows with context length. This motivates two complementary lines of work: **smarter KV-cache management** (H2O, SnapKV, StreamingLLM, Quest, KVzip) and **alternative memory mechanisms at the architecture level** (BDH / BDH-GPU).

## 6. Results & Comparison Disclaimer

> **Published Results — Not Reproduced:** All BDH / BDH-GPU figures come from the original research paper (Kosowski et al., 2025) and are shown for comparison only. They were **not reproduced** by our project.
>
> **Our Interactive Demo:** Results shown for the KV-cache policies (Full Cache, Sliding Window, H2O, SnapKV, StreamingLLM) are generated by **our own simulation pipeline** and should not be interpreted as reproductions of the original papers' full experimental evaluations.

This distinction is enforced in the data layer itself — see `data/precomputed/` below.

---

## Project Structure

```
CacheQuake/
├── README.md                                # you are here
├── research/                                # Paper notes and primary-source grounding
│   ├── papers/
│   │   ├── h2o.md                           # H2O — Heavy-Hitter Oracle
│   │   ├── streamingllm.md                  # StreamingLLM — attention sinks
│   │   ├── snapkv.md                        # SnapKV — observation-window voting
│   │   ├── quest.md                         # Quest — query-aware page sparsity
│   │   ├── kvzip.md                         # KVzip — query-agnostic compression
│   │   └── dragon_hatchling_bdh.md          # our primary BDH notes — quotes + page refs
│   └── citations.md                         # full reference list (arXiv IDs, venues, code links)
└── data/
    └── precomputed/                         # ONLY non-live data lives here, always labeled
        ├── accuracy_vs_budget.json          # our own precomputed sweep results
        └── bdh_published_claims.json        # BDH paper's numbers, source-cited, "not reproduced by us"
```

### `research/papers/`
Per-paper notes covering: core idea, problem, observation, method, key results, limitations, and how each method relates to the others. `dragon_hatchling_bdh.md` additionally includes direct quotes with source attribution, since BDH is the primary architecture-level source for this project.

### `research/citations.md`
Full bibliographic record (authors, venue, year, arXiv ID, code repository) for all six papers referenced across the notes and the interactive demo.

### `data/precomputed/accuracy_vs_budget.json`
Accuracy-vs-KV-budget sweep (5%–100%) for Full Cache, Sliding Window, H2O, SnapKV, and StreamingLLM. Explicitly labeled `"OUR SIMULATION — NOT FROM ORIGINAL PAPERS"` with `reproduced_from_paper: false` in its metadata — these are demo/illustrative values from our own pipeline, not measurements copied from any paper.

### `data/precomputed/bdh_published_claims.json`
Structured, source-cited claims about BDH / BDH-GPU taken directly from Kosowski et al. (2025), labeled `"PUBLISHED, NOT REPRODUCED BY US"`. Where the original paper only makes a qualitative claim (e.g., "rivals GPT2-architecture Transformer performance") rather than reporting a single number, the field is left `null` with an explanatory note rather than inventing a figure.

---

## Research Evidence

This project is grounded in six primary sources:

1. **H2O** — Heavy-Hitter Oracle for Efficient Generative Inference of Large Language Models (Zhang et al., NeurIPS 2023 · arXiv:2306.14048)
2. **StreamingLLM** — Efficient Streaming Language Models with Attention Sinks (Xiao et al., ICLR 2024 · arXiv:2309.17453)
3. **SnapKV** — LLM Knows What You Are Looking for Before Generation (Li et al., 2024 · arXiv:2404.14469)
4. **Quest** — Query-Aware Sparsity for Efficient Long-Context LLM Inference (Tang et al., ICML 2024 · arXiv:2406.10774)
5. **KVzip** — Query-Agnostic KV Cache Compression with Context Reconstruction (Kim et al., NeurIPS 2025 · arXiv:2505.23416)
6. **The Dragon Hatchling (BDH)** — The Missing Link between the Transformer and Models of the Brain (Kosowski et al., 2025 · arXiv:2509.26507)

Full citation details, including code repositories, are in `research/citations.md`.

## AI Disclosure

AI tools were used during the research and documentation process for brainstorming, explanation, drafting, and language refinement. Technical claims and research findings were checked against the cited primary sources, and all BDH-related figures are explicitly marked as published (not reproduced) throughout this repository.

---

*Submitted for DataForge 2026 · Pathway × Rime · "Explain the Frontier" — Team Game of Codes.*
>>>>>>> 7991cfe02243c722b231f8df39b08dfdc8d73bec
