# CacheQuake — Backend Setup Guide

> **For judges hitting the deployed public URL:** You need zero setup.
> Open the URL, use the web UI, done. Everything below is for local
> development or reproducing our precomputed data from scratch.

---

## Prerequisites

| Requirement | Version tested | Notes |
|-------------|---------------|-------|
| Python | **3.11 – 3.14** | Tested on 3.14.4 (Windows). 3.11–3.13 also fine. |
| OS | Windows 11 / Linux | Paths shown as PowerShell; bash equivalents identical |
| Disk | ~200 MB | PyTorch CPU wheel is large |
| RAM | 512 MB | Toy model; CPU-only; no GPU required |

> **Python 3.14 + pydantic note:** `pydantic==2.13.5` (pinned in `requirements.txt`)
> ships a prebuilt `cp314` wheel for `pydantic-core` — no Rust toolchain needed.
> Earlier pins (≤2.11.x) fall back to source compilation and fail without Rust.

No GPU, no CUDA, no Docker required for local development.

---

## Quick start (local development)

### 1. Create and activate a virtual environment

**Windows (PowerShell):**
```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
```

> **Windows troubleshooting — execution policy error:**
> If you see *"cannot be loaded because running scripts is disabled"*, run this
> once in your PowerShell session before activating:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
> ```
> This only affects the current session and does not change your system policy.

**Linux / macOS:**
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

Expected output ends with:
```
Successfully installed ... fastapi-0.115.12 pydantic-2.13.5 pydantic-core-2.46.5
    torch-2.14.0 uvicorn-0.34.3 ...
```
All packages install from prebuilt wheels — **no compilation step**, even on Python 3.14.

> `torch` is the CPU-only wheel (~124 MB). First install takes 1–3 minutes on a
> typical connection. Subsequent installs use pip's wheel cache and are instant.

### 3. Run the test suite

```bash
pytest tests/ -v
```

**What "success" looks like:**
```
72 passed, 5 warnings in ~17s
```

The 5 warnings are all from third-party internals — none affect correctness:

| Warning | Source | Notes |
|---------|--------|-------|
| `StarletteDeprecationWarning`: use `httpx2` | `fastapi/testclient.py` | Test-only; no runtime impact |
| `DeprecationWarning`: `anyio.abc.BlockingPortal` | `starlette/testclient.py` | Internal to starlette |
| `DeprecationWarning`: `asyncio.iscoroutinefunction` deprecated in 3.16 | `fastapi/routing.py` | FastAPI internals; no action needed |
| `UserWarning`: Failed to initialize NumPy | `torch` (no numpy in fresh venv) | Harmless; numpy is not required |


### 4. Start the FastAPI server

```bash
uvicorn app.main:app --reload --port 8000
```

On startup you'll see one of:
```
[CacheQuake] Loaded trained weights from .../model_weights/toy_transformer.pt
```
or:
```
[CacheQuake] No checkpoint found -- using randomly initialized weights.
```

The server is ready when you see `Application startup complete.`

### 5. Test the server is alive

```bash
curl http://localhost:8000/health
```

Expected: `{"status":"ok","vocab":{...},"model":{...},"cache_policies":[...]}`

### 6. Run a simulation (example request)

```bash
curl -X POST http://localhost:8000/simulate \
  -H "Content-Type: application/json" \
  -d '{"policy":"sliding_window","window_size":32,"num_sink_tokens":4,"n_facts":3,"seq_len":120,"question_target":0,"seed":42}'
```

Expected: a JSON object with `episode` and `simulation` top-level keys,
`simulation.steps` containing per-token cache snapshots, and
`simulation.correct` indicating whether the model retrieved the right fact.

---

## Reproducing precomputed data from scratch

These steps are only needed if you want to regenerate
`data/precomputed/accuracy_vs_budget.json` (e.g., after retraining).

### Step 1 — Train the toy model

```bash
python scripts/train_toy.py
```

- Runtime: ~140 seconds (CPU, 3,000 steps)
- Output: `model_weights/toy_transformer.pt` + `model_weights/training_metadata.json`
- **Honesty label:** This is a short training run on our own synthetic data,
  NOT a pretrained language model. See `training_metadata.json` for exact details.

**Training version history (for reproducibility):**

| Version | Issue | Fix |
|---------|-------|-----|
| v1 | `make_batch` truncated to `seq_len=120` ending at `?`. Answer digits never in training data. Model predicted `'t'` after `?`. Accuracy = 0.0. | — |
| v2 | Appended `answer[0]` to sequence. But full-sequence loss diluted retrieval signal across 118 filler positions. Model collapsed to always predicting `'2'`. Accuracy = ~12% (base rate). | — |
| v3 (current, final) | Focused loss: only the `?` position contributes to loss (all other targets = PAD). 5,000 steps. Model receives undiluted retrieval gradient. | This is what `scripts/train_toy.py` now contains. |

The `training_metadata.json` file records `"version": "v2 (answer-digit fix applied)"` so the checkpoint is unambiguously identifiable.


### Step 2 — Generate the accuracy sweep

```bash
python scripts/generate_accuracy_sweep.py
```

- Runtime: ~5–10 minutes (80 episodes × 4 policies × 6 budgets)
- Output: `data/precomputed/accuracy_vs_budget.json`
- Uses eval seeds starting at 100 (training used seed 42) to avoid
  measuring memorized training examples.

> **Lock note:** `accuracy_vs_budget.json` is the file the frontend and
> one-page summary cite directly. Do not silently regenerate it after those
> documents reference specific numbers — flag to the team lead first.

---

## What requires local setup vs. what works with zero setup

| Task | Requires local setup? | Notes |
|------|-----------------------|-------|
| Use the web demo (UI) | **No** | Public URL, zero setup |
| Hit `/health` or `/simulate` directly | **No** | Same public URL |
| Run `pytest` | Yes | Python + pip install |
| Retrain the model | Yes | Python + ~3 min CPU time |
| Regenerate accuracy sweep | Yes | Python + ~10 min CPU time |
| Inspect source code | **No** | GitHub repo is public |

---

## File layout reference

```
backend/
├── requirements.txt            # pinned dependencies
├── README.md                   # API contract + architecture
├── SETUP.md                    # this file
├── model_weights/
│   ├── toy_transformer.pt      # trained checkpoint (loaded at startup)
│   └── training_metadata.json  # exact training details (steps, lr, seed, …)
├── data/precomputed/
│   ├── accuracy_vs_budget.json # LOCKED: final sweep results (all 4 policies)
│   └── bdh_published_claims.json  # Qualitative BDH paper claims, cited + labeled
├── scripts/
│   ├── train_toy.py            # reproduce the training run
│   └── generate_accuracy_sweep.py  # reproduce the precomputed sweep
├── app/
│   ├── main.py                 # FastAPI app
│   ├── model/                  # ToyTransformer, attention, vocab
│   ├── cache_policies/         # full_cache, sliding_window, heavy_hitter, bdh_inspired_state
│   ├── simulation/             # runner.py (token-by-token episode loop)
│   └── tasks/                  # needle_haystack.py (synthetic data)
└── tests/
    ├── test_smoke.py           # Day 1 smoke tests
    ├── test_day2.py            # Day 2 regression tests (25 tests)
    └── test_day3.py            # Day 3 regression tests (25 tests)
```
