# CacheQuake — Backend

Simulation backend for the **CacheQuake** interactive KV-cache explainer.
**DataForge 2026 — Pathway × Rime hackathon track.**

---

## One-sentence claim this project teaches

> A Transformer's KV cache grows linearly with every token it has ever seen
> because it stores an exact copy of the past; eviction and compression trade
> that exactness for a bounded budget, and architectures like BDH remove the
> growth altogether by replacing the cache with a fixed-size associative state
> that overwrites itself instead of appending.

---

## Quick start

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
# → GET http://localhost:8000/health
```

Run smoke tests:
```bash
cd backend
pytest tests/test_smoke.py -v
```

---

## Project layout

```
backend/
├── requirements.txt          # pinned deps (torch CPU, fastapi, uvicorn)
├── README.md                 # this file
└── app/
    ├── main.py               # FastAPI app — /health + /simulate live; /step Day 3
    ├── model/
    │   ├── vocab.py          # 44-symbol char-level vocabulary
    │   ├── attention.py      # MultiHeadAttention with cache_mask hook
    │   └── toy_transformer.py# 4-layer decoder-only Transformer
    ├── cache_policies/
    │   ├── base.py           # abstract CachePolicy interface
    │   ├── full_cache.py     # ✅ implemented — keep everything
    │   ├── sliding_window.py # ✅ implemented — sink + recent window (Day 2)
    │   ├── heavy_hitter.py   # 🔲 stub — Day 3
    │   └── bdh_inspired_state.py # 🔲 stub — Day 3 (toy layer, not BDH)
    ├── simulation/
    │   └── runner.py         # ✅ implemented — token-by-token prefill loop
    └── tasks/
        └── needle_haystack.py# ✅ implemented — synthetic data generator
```

---

## Tensor shape contract (stable API for frontend)

This section is the authoritative reference for the frontend developer.
All shapes below are guaranteed not to change until Day 2.

### Vocabulary (`app/model/vocab.py`)

| Symbol | Value | Notes |
|--------|-------|-------|
| `VOCAB_SIZE` | `44` | 42 printable + PAD + UNK |
| `PAD_ID` | `42` | Padding token |
| `UNK_ID` | `43` | Unknown character |
| Symbols | `a-z 0-9 space .,?!'` | 42 chars, no uppercase, no BPE |

```python
from app.model.vocab import encode, decode, VOCAB_SIZE
ids: list[int] = encode("hello world")  # list of ints in [0, 39]
text: str       = decode(ids)           # reconstructed string
```

### Model spec

| Parameter | Value |
|-----------|-------|
| `vocab_size` | 44 |
| `d_model` | 64 |
| `n_heads` | 4 |
| `d_head` = `d_model // n_heads` | **16** |
| `n_layers` | 4 |
| `max_seq_len` | 512 |

### `ToyTransformer.forward()` shapes

```
Inputs:
  token_ids   : int[B, T]
  past_caches : List[n_layers] of (K_past, V_past) or None
                  K_past : float[B, H, T_past, d_head]
                  V_past : float[B, H, T_past, d_head]
  cache_masks : List[n_layers] of bool[B, T_past] or None
                  True  = this cached position is visible
                  False = this position has been evicted

Outputs:
  logits         : float[B, T, vocab_size]
  present_caches : List[n_layers] of (K_new, V_new)
                     K_new : float[B, H, T, d_head]   ← current tokens only
                     V_new : float[B, H, T, d_head]   ← current tokens only
```

### `CachePolicy.update()` contract

```
Inputs:
  step       : int
  layer_idx  : int
  k          : float[B, H, T_new, d_head]
  v          : float[B, H, T_new, d_head]
  past_cache : (K_past, V_past) or None

Outputs (tuple of 3):
  K_stored   : float[B, H, T_kept, d_head]
  V_stored   : float[B, H, T_kept, d_head]
  cache_mask : bool[B, T_kept]   True=visible, False=evicted
```

### `NeedleHaystackEpisode` fields

```python
episode.token_ids       # list[int]       — full encoded sequence
episode.answer          # str             — ground-truth answer digits
episode.fact_positions  # dict[str, int]  — {vault_name: start_token_index}
episode.question_start  # int             — token index where question begins
episode.text            # str             — human-readable decoded sequence
episode.vault_codes     # dict[str, str]  — {vault_name: code_string}
```

---

## REST API contract

Base URL: `http://localhost:8000`

### `GET /health`

Always returns 200. Frontend should poll this before enabling the UI.

```json
{
  "status": "ok",
  "vocab": {
    "vocab_size": 44,
    "pad_id": 42,
    "unk_id": 43,
    "symbols": "abcdefghijklmnopqrstuvwxyz0123456789 .,?!'"
  },
  "model": {
    "d_model": 64,
    "n_heads": 4,
    "n_layers": 4,
    "max_seq_len": 512,
    "n_parameters": <int>
  },
  "cache_policies": [
    "full_cache",
    "sliding_window",
    "heavy_hitter",
    "bdh_inspired_state"
  ]
}
```

### `POST /simulate` — **Live as of Day 2**

Run a full needle-in-haystack episode with a chosen cache policy.

**Request body:**
```json
{
  "policy": "full_cache",
  "window_size": 64,
  "num_sink_tokens": 4,
  "n_facts": 3,
  "seq_len": 200,
  "question_target": 0,
  "seed": 42
}
```

| Field | Type | Default | Notes |
|-------|------|---------|-------|
| `policy` | str | `"full_cache"` | `"full_cache"`, `"sliding_window"`, `"heavy_hitter"`, `"bdh_inspired_state"` |
| `window_size` | int | `64` | `sliding_window` only, range `[1, 512]` |
| `num_sink_tokens` | int | `4` | `sliding_window` only, range `[0, 16]` |
| `budget` | int | `64` | `heavy_hitter` only, range `[1, 512]` |
| `state_size` | int | `32` | `bdh_inspired_state` only, range `[4, 128]` |
| `decay` | float | `0.9` | `bdh_inspired_state` only, range `[0.0, 1.0)` |
| `n_facts` | int | `3` | Facts injected, range `[1, 8]` |
| `seq_len` | int | `200` | Total tokens, range `[32, 512]` |
| `question_target` | int | `0` | Which fact to ask about (< n_facts) |
| `seed` | int | `42` | For reproducible episodes |

**Response body (STABLE — frontend contract):**
```json
{
  "episode": {
    "text": "the passcode for vault 2 is 7291 ...",
    "token_ids": [19, 7, 4, ...],
    "fact_positions": {"vault 2": 47},
    "question_start": 183,
    "answer": "7291"
  },
  "simulation": {
    "policy": "sliding_window",
    "policy_params": {"window_size": 64, "num_sink_tokens": 4},
    "steps": [
      {
        "step": 0,
        "token_id": 19,
        "token_char": "t",
        "visible_token_indices": [0],
        "cache_size_tokens": 1,
        "cache_size_bytes": 2048
      }
    ],
    "final_answer": "7",
    "ground_truth": "7291",
    "correct": true,
    "policy_info": {
      "policy": "sliding_window",
      "window_size": 64,
      "num_sink_tokens": 4,
      "tokens_cached": 68,
      "tokens_seen": 200,
      "evictions": 132
    }
  }
}
```

**Key fields:**
- `visible_token_indices`: global token indices (0-based) currently in the cache at this step. Render as a heatmap over the input sequence.
- `cache_size_bytes`: `cache_size_tokens × 2048` (= 4 layers × 2 (K+V) × 4 heads × 16 d_head × 4 bytes).
- `correct`: `True` if `final_answer == ground_truth[0]` (first-character match; model is untrained so full-string match is not expected).

**Error responses:**
- `400`: Unknown policy name or `question_target >= n_facts`.
- `422`: Pydantic validation error (malformed request body).

### `POST /step` — **501 until Day 3**

Streaming single-step companion to `/simulate`.  Will advance the
simulation by one token and return that step's cache state + logits.

---

## Four cache policies

| Policy | File | Memory | Status |
|--------|------|--------|--------------|
| Full cache | `full_cache.py` | O(T) — grows forever | ✅ Day 1 |
| Sliding window | `sliding_window.py` | O(W+S) — bounded | ✅ Day 2 |
| Heavy hitter | `heavy_hitter.py` | O(B) — fixed budget | ✅ Day 3 |
| BDH-inspired state* | `bdh_inspired_state.py` | O(S) — **constant** | ✅ Day 3 |

\* **Disclaimer**: `bdh_inspired_state.py` is a *toy layer inspired by the
BDH architecture* (arXiv:2509.26507, Pathway Inc.).  It is not the real BDH
model.  We do not reproduce or claim to reproduce BDH's architecture, weights,
or performance.

---

## BDH citation

> "The Dragon Hatchling: The Missing Link between the Transformer and Models
> of the Brain." arXiv:2509.26507. Pathway Inc.

The real BDH paper is cited and explained in the project's UI explainer text.
Our toy layer uses BDH's *conceptual insight* (fixed-size associative state
that overwrites instead of appending) purely for educational demonstration.
See `data/precomputed/bdh_published_claims.json` for sourced qualitative claims
and an explicit list of simplifications we made vs. the real architecture.

---

## Model state and training

The toy model ships **lightly trained** on our own synthetic needle-haystack
task — the minimum required for the accuracy-vs-budget curves to be
pedagogically meaningful.

| Field | Value |
|-------|-------|
| Training version | v3 (focused answer-position loss) |
| Training steps | 5,000 |
| Batch size | 8 episodes |
| Optimizer | AdamW, lr=3e-3, weight_decay=1e-2, grad_clip=1.0 |
| Loss masking | Only the `?` → answer_digit position; all other targets = PAD |
| Data | `NeedleHaystackTask` synthetic episodes (same task as demo) |
| Duration | ~395 seconds, CPU |
| Final loss | ~1.09 (from random baseline of 2.30 = log(10)) |
| Checkpoint | `model_weights/toy_transformer.pt` |

**Honesty label:** this is NOT a pretrained language model and NOT a
benchmark-evaluated model. It is a short training run on our own synthetic
data. See `model_weights/training_metadata.json` for the exact training
record, including a `training_fix_note` documenting the v1/v2/v3 iteration.

**Training iteration history (documented for reproducibility):**

| Version | Problem | Fix |
|---------|---------|-----|
| v1 | Answer digits truncated off; model predicted `'t'` always. Accuracy = 0% | — |
| v2 | Answer appended but 118 noisy positions diluted gradient; model predicted `'2'` always. Accuracy = ~11% (base rate) | — |
| v3 ✅ | Focused loss: only `?` position contributes. Loss 2.30→1.09. | Current checkpoint |

**Locked accuracy numbers** (80 episodes, eval seed base=100, v3 checkpoint):

| Policy | budget=4 | budget=16 | budget=32 | budget=64 | budget=96 | budget=∞ |
|--------|----------|-----------|-----------|-----------|-----------|-----------|
| full_cache | — | — | — | — | — | **37.5%** |
| sliding_window | 6.3% | 5.0% | 7.5% | 30.0% | 26.3% | — |
| heavy_hitter | 8.8% | 2.5% | **51.3%** | **62.5%** | 38.8% | — |
| bdh_inspired_state | 13.8% | 8.8% | 8.8% | 13.8% | 6.3% | — |

Notable findings in this data:
- `heavy_hitter` at budget=32-64 **outperforms** `full_cache` — by selectively retaining the highest-attention (fact) tokens and discarding noisy haystack tokens, it attends more precisely than a full unbounded cache.
- `bdh_inspired_state` shows roughly flat accuracy across state sizes — consistent with the overwrite semantics (no budget → accuracy growth without exact token storage).
- `sliding_window` recovers toward `full_cache` as budget approaches sequence length.

To retrain from scratch: `python scripts/train_toy.py` (see `SETUP.md` for the full version history).


---

## Other approaches to the KV-cache problem
*(Cited and compared; not simulated live in this demo.)*

**Compression / quantization:** Rather than evicting entire tokens, methods
like KVQuant (Hooper et al., 2024) reduce the per-token memory footprint by
quantizing key and value tensors to 2–4 bits. This keeps the full history
visible at lower precision rather than discarding tokens entirely. We do not
simulate compression because it would require changing the tensor dtype mid-run
and would conflate two orthogonal axes (precision vs. eviction) in the UI.

**Retrieval-augmented generation (RAG):** Instead of keeping past tokens in
an in-context cache, RAG systems (Lewis et al., 2020; Borgeaud et al., 2022)
offload long-range memory to an external vector store and retrieve relevant
chunks at query time. Memory footprint is O(1) in context but shifts the cost
to retrieval latency and index storage. Unlike our fixed-size recurrent state,
RAG preserves exact token representations — it just moves them off the GPU.

**Linear attention / state-space models:** Models such as RWKV (Peng et al.,
2023), RetNet (Sun et al., 2023), and Mamba (Gu & Dao, 2023) reformulate
attention to run in O(1) recurrent state per step rather than O(T). This is
the same high-level goal as our BDH-inspired toy layer, but achieved by
changing the attention *kernel* (replacing softmax with a linear or selective
kernel) rather than retrofitting a fixed-size buffer onto a standard
Transformer. These models cannot be compared directly to our policies because
they require retraining with the new kernel.

**Hybrid eviction + sink tokens (StreamingLLM):** Xiao et al. (2023) show
that retaining a small number of initial "attention sink" tokens alongside
a sliding window dramatically improves perplexity versus a pure sliding window.
Our `sliding_window.py` implements this (the `num_sink_tokens` parameter) and
is the direct live demonstration of this finding in the UI.

---

## Deployment notes (Hugging Face Spaces)

- The backend is CPU-only (`torch==2.3.1` without CUDA).
- The FastAPI app is served by Uvicorn on the HF Spaces default port.
- See `SETUP.md` for local reproduction instructions.
- `model_weights/toy_transformer.pt` must be present for the trained model
  to load at startup; the server falls back to random init if the file is absent.
