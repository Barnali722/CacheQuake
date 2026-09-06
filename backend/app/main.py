# backend/app/main.py
"""
CacheQuake — FastAPI backend entry point.

Running locally:
    cd backend
    uvicorn app.main:app --reload --port 8000

Endpoints today:
    GET  /health      — confirms the service is alive; returns model metadata.
    POST /simulate    — 501 Not Implemented (Day 2 task)
    POST /step        — 501 Not Implemented (Day 2 task)

CORS:
    All origins are allowed during hackathon development.  Restrict before
    production if the project is open-sourced beyond HF Spaces.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .model.vocab import vocab_info
from .model.toy_transformer import ToyTransformer

# ---------------------------------------------------------------------------
# Application setup
# ---------------------------------------------------------------------------

app = FastAPI(
    title="CacheQuake Backend",
    description=(
        "Simulation backend for the CacheQuake KV-cache explainer. "
        "DataForge 2026 — Pathway × Rime hackathon track."
    ),
    version="0.1.0",
)

# Allow all origins during development so the React dev server can reach us.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Shared model instance (initialised once at startup, CPU only)
# ---------------------------------------------------------------------------

# Instantiate with the confirmed hackathon spec.
# This is the single model shared across all simulation requests.
# It is *not* trained — weights are randomly initialised, which is fine
# because our task is to demonstrate cache *mechanics*, not model quality.
_model = ToyTransformer(
    vocab_size  = 44,   # 42 printable symbols + PAD + UNK — matches vocab.py VOCAB_SIZE
    d_model     = 64,
    n_heads     = 4,
    n_layers    = 4,
    max_seq_len = 512,
)
_model.eval()  # disable any training-time behaviour (dropout etc.)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/health", summary="Health check")
async def health() -> dict:
    """Return service status and model metadata.

    This lets the frontend confirm the backend is reachable and lets a
    developer quickly check that the model was instantiated with the right
    spec before writing any simulation code.

    Response schema:
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
            "n_heads":      4,   # stored separately since model_info() has a bug to fix later
            "n_layers":     _model.n_layers,
            "max_seq_len":  _model.max_seq_len,
            "n_parameters": _model.count_parameters(),
        },
        "cache_policies": [
            "full_cache",
            "sliding_window",
            "heavy_hitter",
            "bdh_inspired_state",  # toy layer inspired by BDH, not BDH itself
        ],
    }


@app.post("/simulate", summary="Run a full needle-in-haystack simulation (not yet implemented)")
async def simulate() -> JSONResponse:
    """Run one complete episode with a chosen cache policy.

    NOT YET IMPLEMENTED — Day 2 task.

    When implemented, this endpoint will:
        1. Accept a JSON body specifying:
               policy       : str   — one of the four cache policy names
               n_facts      : int   — number of facts to inject
               seq_len      : int   — target sequence length
               question_target : int — which fact the question asks about
               window_size  : int   — for sliding_window policy
               budget       : int   — for heavy_hitter policy
               state_size   : int   — for bdh_inspired_state policy
        2. Generate a needle-in-haystack episode.
        3. Run the toy Transformer token-by-token, collecting:
               - KV cache state per step per layer
               - memory_tokens_used() per step
               - Per-step logits over the vocabulary
        4. Return:
               token_ids, fact_positions, question_start,
               per_step_memory, per_step_top_token,
               final_answer, ground_truth_answer, correct (bool),
               policy_info.

    Returns:
        501 Not Implemented
    """
    return JSONResponse(
        status_code=501,
        content={"error": "Not Implemented", "detail": "/simulate — Day 2 task"},
    )


@app.post("/step", summary="Advance one generation step (not yet implemented)")
async def step() -> JSONResponse:
    """Advance the simulation by one token.

    NOT YET IMPLEMENTED — Day 2 task.

    This is the streaming companion to /simulate.  Instead of running the
    full episode server-side, the frontend will call /step in a loop,
    receiving one token's worth of state at a time.  This allows the UI to
    animate the cache growing/evicting in real time without waiting for the
    full run.

    When implemented, session state will be managed server-side (likely via
    an in-memory dict keyed by session_id) so the cache tensors persist
    across calls.

    Returns:
        501 Not Implemented
    """
    return JSONResponse(
        status_code=501,
        content={"error": "Not Implemented", "detail": "/step — Day 2 task"},
    )
