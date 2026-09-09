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
