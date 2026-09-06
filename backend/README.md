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
    ├── main.py               # FastAPI app — /health live, /simulate & /step stubbed
    ├── model/
    │   ├── vocab.py          # 40-symbol char-level vocabulary
    │   ├── attention.py      # MultiHeadAttention with cache_mask hook
    │   └── toy_transformer.py# 4-layer decoder-only Transformer
    ├── cache_policies/
    │   ├── base.py           # abstract CachePolicy interface
    │   ├── full_cache.py     # ✅ implemented — keep everything
    │   ├── sliding_window.py # 🔲 stub — Day 2
    │   ├── heavy_hitter.py   # 🔲 stub — Day 2
    │   └── bdh_inspired_state.py # 🔲 stub — Day 2/3 (toy layer, not BDH)
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
| `vocab_size` | 40 |
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
    "vocab_size": 40,
    "pad_id": 38,
    "unk_id": 39,
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

### `POST /simulate` — **501 until Day 2**

Will accept a JSON body and return per-step memory + retrieval results.
Planned request schema (subject to revision):

```json
{
  "policy": "full_cache",
  "n_facts": 3,
  "seq_len": 256,
  "question_target": 1,
  "window_size": 64,
  "budget": 64,
  "state_size": 32
}
```

### `POST /step` — **501 until Day 2**

Streaming single-step companion to `/simulate`.  Will advance the
simulation by one token and return that step's cache state + logits.

---

## Four cache policies

| Policy | File | Memory | Day 1 status |
|--------|------|--------|--------------|
| Full cache | `full_cache.py` | O(T) — grows forever | ✅ Implemented |
| Sliding window | `sliding_window.py` | O(W) — fixed budget | 🔲 Stub |
| Heavy hitter | `heavy_hitter.py` | O(B) — fixed budget | 🔲 Stub |
| BDH-inspired state* | `bdh_inspired_state.py` | O(S) — **constant** | 🔲 Stub |

\* **Disclaimer**: `bdh_inspired_state.py` is a *toy layer inspired by the
BDH architecture* (arXiv:2509.26507, Pathway Inc.).  It is not the real BDH
model.  We do not reproduce or claim to reproduce BDH's architecture, weights,
or performance.

---

## BDH citation

> BDH: Bounded-state Decoding and Hybrid Architectures.
> arXiv:2509.26507. Pathway Inc.

The real BDH paper is cited and explained in the project's UI explainer text.
Our toy layer uses BDH's *conceptual insight* (fixed-size associative state
that overwrites instead of appending) purely for educational demonstration.

---

## Deployment notes (Hugging Face Spaces)

- The backend is CPU-only (`torch==2.3.1` without CUDA).
- The FastAPI app is served by Uvicorn on the HF Spaces default port.
- A `Dockerfile` will be added on Day 3 once the full simulation loop is working.
