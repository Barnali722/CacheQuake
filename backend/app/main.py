# backend/app/main.py
"""
CacheQuake — FastAPI backend entry point.

Running locally:
    cd backend
    uvicorn app.main:app --reload --port 8000

Endpoints:
    GET  /health      — service alive check; returns model + vocab metadata.
    POST /simulate    — run a full needle-in-haystack simulation.
    POST /step        — 501 Not Implemented (Day 3 streaming companion).

CORS:
    All origins allowed during hackathon development.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .model.vocab import vocab_info
from .model.toy_transformer import ToyTransformer
from .cache_policies.full_cache import FullCachePolicy
from .cache_policies.sliding_window import SlidingWindowPolicy
from .cache_policies.heavy_hitter import HeavyHitterPolicy
from .cache_policies.bdh_inspired_state import BDHInspiredState
from .tasks.needle_haystack import NeedleHaystackTask
from .simulation.runner import run_episode

# ---------------------------------------------------------------------------
# Application setup
# ---------------------------------------------------------------------------

app = FastAPI(
    title="CacheQuake Backend",
    description=(
        "Simulation backend for the CacheQuake KV-cache explainer. "
        "DataForge 2026 — Pathway × Rime hackathon track."
    ),
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Mount static data directory for precomputed JSON files
# ---------------------------------------------------------------------------

import os as _os
_DATA_DIR = _os.path.normpath(_os.path.join(_os.path.dirname(__file__), "..", "data"))
if _os.path.exists(_DATA_DIR):
    app.mount("/data", StaticFiles(directory=_DATA_DIR), name="data")
    print(f"[CacheQuake] Mounted static data directory: {_DATA_DIR}")

# ---------------------------------------------------------------------------
# Shared model instance (one per process, CPU only)
# Loads trained weights if model_weights/toy_transformer.pt exists;
# falls back to random initialization if not (with clear logging).
# ---------------------------------------------------------------------------

import os, json as _json

_WEIGHTS_DIR  = os.path.join(os.path.dirname(__file__), "..", "model_weights")
_CKPT_PATH    = os.path.normpath(os.path.join(_WEIGHTS_DIR, "toy_transformer.pt"))
_META_PATH    = os.path.normpath(os.path.join(_WEIGHTS_DIR, "training_metadata.json"))

_model = ToyTransformer(
    vocab_size  = 44,   # 42 printable symbols + PAD + UNK — matches vocab.py VOCAB_SIZE
    d_model     = 64,
    n_heads     = 4,
    n_layers    = 4,
    max_seq_len = 512,
)

if os.path.exists(_CKPT_PATH):
    _model.load_state_dict(
        __import__("torch").load(_CKPT_PATH, map_location="cpu", weights_only=True)
    )
    _model_state = "lightly_trained"
    _training_meta = _json.load(open(_META_PATH)) if os.path.exists(_META_PATH) else {}
    print(f"[CacheQuake] Loaded trained weights from {_CKPT_PATH}")
else:
    _model_state   = "randomly_initialized"
    _training_meta = {}
    print("[CacheQuake] No checkpoint found — using randomly initialized weights.")

_model.eval()  # no dropout / batch-norm training behaviour

# ---------------------------------------------------------------------------
# Request / Response Schemas (Pydantic)
# ---------------------------------------------------------------------------

class SimulateRequest(BaseModel):
    """Request body for POST /simulate.

    All fields documented here are the stable contract for the frontend.
    Do not add required fields without a version bump.
    """

    policy: str = Field(
        default="full_cache",
        description=(
            "Which cache policy to use. "
            "One of: 'full_cache', 'sliding_window'. "
            "('heavy_hitter' and 'bdh_inspired_state' are Day 3.)"
        ),
    )
    # sliding_window parameters (ignored for other policies)
    window_size: int = Field(
        default=64,
        ge=1,
        le=512,
        description="Number of recent tokens to keep (sliding_window only).",
    )
    num_sink_tokens: int = Field(
        default=4,
        ge=0,
        le=16,
        description="Number of initial tokens kept forever (sliding_window only).",
    )
    # heavy_hitter parameters (ignored for other policies)
    budget: int = Field(
        default=64,
        ge=1,
        le=512,
        description="Number of high-attention-score tokens to keep (heavy_hitter only).",
    )
    # bdh_inspired_state parameters (ignored for other policies)
    state_size: int = Field(
        default=32,
        ge=4,
        le=128,
        description="Number of fixed memory slots (bdh_inspired_state only).",
    )
    decay: float = Field(
        default=0.9,
        ge=0.0,
        lt=1.0,
        description="Forgetting factor for the associative memory (bdh_inspired_state only).",
    )
    # Episode generation parameters
    n_facts: int = Field(
        default=3,
        ge=1,
        le=8,
        description="Number of vault facts to inject into the sequence.",
    )
    seq_len: int = Field(
        default=200,
        ge=32,
        le=512,
        description="Target total sequence length in tokens.",
    )
    question_target: int = Field(
        default=0,
        ge=0,
        description="Index (0-based) of the fact the question asks about.",
    )
    seed: int = Field(
        default=42,
        description="Random seed for reproducible episode generation.",
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/health", summary="Health check")
async def health() -> dict:
    """Return service status and model metadata.

    Response schema (stable — frontend may cache this):
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
      "cache_policies": ["full_cache", "sliding_window", "heavy_hitter", "bdh_inspired_state"]
    }
    ```
    """
    return {
        "status": "ok",
        "vocab":  vocab_info(),
        "model":  {
            "d_model":      _model.d_model,
            "n_heads":      _model.n_heads,
            "n_layers":     _model.n_layers,
            "max_seq_len":  _model.max_seq_len,
            "n_parameters": _model.count_parameters(),
            # model_state tells the frontend which badge to show.
            # "lightly_trained"      — weights loaded from model_weights/toy_transformer.pt
            # "randomly_initialized" — no checkpoint found at startup
            "model_state":    _model_state,
            "training_info":  _training_meta.get("training", {}),
        },
        "cache_policies": [
            "full_cache",
            "sliding_window",
            "heavy_hitter",
            "bdh_inspired_state",    # toy layer inspired by BDH, not BDH itself
        ],
    }


@app.post("/simulate", summary="Run a full needle-in-haystack simulation")
async def simulate(req: SimulateRequest) -> dict:
    """Run one complete episode with the chosen cache policy.

    Request body: see SimulateRequest schema above.

    Response schema (stable — frontend contract):
    ```json
    {
      "episode": {
        "text": "...",
        "token_ids": [7, 4, ...],
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
            "token_id": 7,
            "token_char": "h",
            "visible_token_indices": [0],
            "cache_size_tokens": 1,
            "cache_size_bytes": 2048
          },
          ...
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

    Notes:
    - `visible_token_indices`: list of global token positions (0-based) that
      the cache holds at this step.  Use this to colour the input sequence.
    - `cache_size_bytes`: computed as tokens × 2048 (= 4 layers × 2 × 4 heads
      × 16 d_head × 4 bytes per float32).
    - `final_answer`: single character (argmax of last-token logits).
    - `correct`: True if `final_answer == ground_truth[0]` (first digit match).
      The model is untrained so full string match is unlikely; first-char is a
      fairer signal of whether the right fact was attended to.

    Raises:
        400: Invalid policy name.
        400: question_target >= n_facts.
        422: Pydantic validation error (malformed request).
    """
    # --- Validate policy name -------------------------------------------
    IMPLEMENTED = {"full_cache", "sliding_window", "heavy_hitter", "bdh_inspired_state"}
    if req.policy not in IMPLEMENTED:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Policy '{req.policy}' is not yet implemented. "
                f"Available today: {sorted(IMPLEMENTED)}"
            ),
        )

    # --- Validate question_target < n_facts --------------------------------
    if req.question_target >= req.n_facts:
        raise HTTPException(
            status_code=400,
            detail=(
                f"question_target={req.question_target} must be < "
                f"n_facts={req.n_facts}"
            ),
        )

    # --- Build the cache policy -------------------------------------------
    if req.policy == "full_cache":
        policy = FullCachePolicy()
        policy_params = {}
    elif req.policy == "sliding_window":
        policy = SlidingWindowPolicy(
            window_size     = req.window_size,
            num_sink_tokens = req.num_sink_tokens,
        )
        policy_params = {
            "window_size":     req.window_size,
            "num_sink_tokens": req.num_sink_tokens,
        }
    elif req.policy == "heavy_hitter":
        policy = HeavyHitterPolicy(budget=req.budget)
        policy_params = {"budget": req.budget}
    else:  # bdh_inspired_state
        # Toy layer inspired by BDH, not BDH itself.
        # d_head and n_heads are model constants; we read from _model.
        policy = BDHInspiredState(
            state_size = req.state_size,
            d_head     = _model.d_model // _model.n_heads,  # 64 // 4 = 16
            n_heads    = _model.n_heads,
            decay      = req.decay,
        )
        policy_params = {
            "state_size": req.state_size,
            "decay":      req.decay,
        }

    # --- Generate the episode ---------------------------------------------
    task    = NeedleHaystackTask(seed=req.seed)
    episode = task.generate(
        n_facts         = req.n_facts,
        seq_len         = req.seq_len,
        question_target = req.question_target,
    )

    # --- Run the simulation -----------------------------------------------
    result = run_episode(
        model         = _model,
        policy        = policy,
        episode       = episode,
        policy_name   = req.policy,
        policy_params = policy_params,
    )

    # --- Serialise to JSON-safe dict --------------------------------------
    # StepRecord contains Python lists/ints — straightforward to serialise.
    steps_json = [
        {
            "step":                  s.step,
            "token_id":              s.token_id,
            "token_char":            s.token_char,
            "visible_token_indices": s.visible_token_indices,
            "cache_size_tokens":     s.cache_size_tokens,
            "cache_size_bytes":      s.cache_size_bytes,
        }
        for s in result.steps
    ]

    return {
        "episode": {
            "text":           result.text,
            "token_ids":      result.token_ids,
            "fact_positions": result.fact_positions,
            "question_start": result.question_start,
            "answer":         result.ground_truth,
        },
        "simulation": {
            "policy":        result.policy_name,
            "policy_params": result.policy_params,
            "steps":         steps_json,
            "final_answer":  result.final_answer,
            "ground_truth":  result.ground_truth,
            "correct":       result.correct,
            "policy_info":   result.policy_info,
        },
    }


@app.post("/step", summary="Advance one generation step (Day 3 — not yet implemented)")
async def step() -> JSONResponse:
    """Single-step streaming companion to /simulate.

    NOT YET IMPLEMENTED — Day 3 task.

    When implemented this will advance a stateful session by one token,
    returning that step's cache snapshot so the UI can animate in real time.
    Session state will be keyed by a session_id returned on first call.

    Returns:
        501 Not Implemented
    """
    return JSONResponse(
        status_code=501,
        content={"error": "Not Implemented", "detail": "/step — Day 3 task"},
    )
