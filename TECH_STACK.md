# CacheQuake — Technology Stack

**Project:** "CacheQuake" — Interactive KV-Cache Explainer  
**Hackathon:** DataForge 2026 (Pathway × Rime)  
**Topic:** Key–Value Caching, Limitations, and Alternate Approaches

---

## Architecture Overview

```
┌──────────────────┐     HTTP/JSON      ┌─────────────────────┐
│   Frontend       │ ◄─────────────────► │   Backend           │
│   (React SPA)    │    /simulate        │   (FastAPI + PyTorch)│
└──────────────────┘    /health          └─────────────────────┘
     │                                              │
     │                                              │
  Vite Build                                 Toy Transformer
     │                                       + Cache Policies
     ▼                                              │
  Static Site                                       ▼
 (Hugging Face)                          Precomputed Data (JSON)
```

**Deployment Target:** Hugging Face Spaces (frontend + backend)  
**Design Philosophy:** CPU-only, educational explainer (not production ML inference)

---

## Frontend Stack

### Core Framework
- **React** `^18.3.1` — UI library for component-based interface
- **React DOM** `^18.3.1` — React rendering for web

### Build Tool
- **Vite** `^5.4.1` — Fast ES module-based build tool and dev server
  - Lightning-fast HMR (Hot Module Replacement)
  - Optimized production builds with rollup
  - Native ES modules in development

### Development Tools
- **ESLint** `^9.9.0` — Code linting and style enforcement
  - `eslint-plugin-react-hooks` `^5.1.0-rc.0` — React Hooks rules
  - `eslint-plugin-react-refresh` `^0.4.9` — React Fast Refresh validation
- **@vitejs/plugin-react** `^4.3.1` — Official Vite plugin for React with Fast Refresh

### Type Definitions (DevDependencies)
- **@types/react** `^18.3.1`
- **@types/react-dom** `^18.3.1`

### Language
- **JavaScript (ES modules)** — Modern ESM syntax, no TypeScript

### Requirements
- **Node.js** `>=18.0.0`

---

## Backend Stack

### Core Framework
- **FastAPI** `0.115.12` — Modern Python web framework for APIs
  - Automatic OpenAPI/Swagger documentation
  - Pydantic validation for request/response schemas
  - Native async support (though we use sync for CPU-bound inference)

### Web Server
- **Uvicorn[standard]** `0.34.3` — Lightning-fast ASGI server
  - Includes `uvloop`, `httptools`, and `websockets` extras for performance
  - Production-ready for single-worker CPU demo

### Machine Learning
- **PyTorch** `>=2.3.0` — Deep learning framework (CPU-only)
  - Tested on 2.3.1+, no CUDA dependency
  - Used for toy Transformer model and tensor operations
  - No GPU acceleration (hackathon demo constraint)

### Data Validation
- **Pydantic** `2.13.5` — Data validation and settings management
  - Schema validation for `/simulate` endpoint requests
  - Type hints with runtime validation
  - Bumped from 2.7.4 for Python 3.14 wheel compatibility

### Testing
- **pytest** `8.2.2` — Python testing framework
  - 72 tests covering all cache policies and endpoints
  - Integration tests using FastAPI TestClient

### HTTP Client (Testing)
- **httpx** `0.28.1` — Async/sync HTTP client
  - Used via `starlette.testclient.TestClient` for endpoint testing
  - Python 3.14 compatible prebuilt wheel

### Language & Runtime
- **Python** `3.11–3.14` — Backend implementation language
  - Tested on Python 3.14.4 (Windows)
  - Type hints throughout codebase
  - All dependencies have prebuilt wheels (no Rust/C++ compilation required)

---

## Key Libraries & Components

### Custom Implementations (Backend)

#### Model Architecture (`app/model/`)
- **ToyTransformer** — 4-layer decoder-only Transformer
  - Vocab size: 44 tokens (42 printable + PAD + UNK)
  - d_model: 64, n_heads: 4, n_layers: 4
  - Max seq len: 512 tokens
  - Trained on needle-in-haystack retrieval task

#### Cache Policies (`app/cache_policies/`)
1. **FullCachePolicy** — Unbounded KV cache (baseline)
2. **SlidingWindowPolicy** — Windowed attention with sink tokens
3. **HeavyHitterPolicy** — Attention-score-based eviction
4. **BDHInspiredState** — Fixed-size associative memory (toy layer inspired by BDH)

#### Task & Simulation (`app/tasks/`, `app/simulation/`)
- **NeedleHaystackTask** — Generates synthetic retrieval episodes
- **run_episode()** — Token-by-token simulation with cache policy hooks

### Frontend Components

Custom React components implementing:
- Interactive cache visualization
- Policy selector and parameter controls
- Token-by-token animation
- Real-time cache size graphs

---

## Development & Deployment Tools

### Version Control
- **Git** — Source control
- **GitHub** — Repository hosting
  - CI/CD via GitHub Actions (`.github/workflows/deploy-frontend.yml`)

### Deployment
- **Hugging Face Spaces** — Static hosting for frontend + backend
  - No Dockerfile required for simple Python+static deployments
  - Auto-deploy from GitHub main branch

### Package Management
- **pip** — Python package installer (backend)
- **npm** — Node package manager (frontend)

---

## Data & Assets

### Precomputed Data (`backend/data/precomputed/`)
- **`accuracy_vs_budget.json`** — Performance curves for each cache policy
- **`bdh_published_claims.json`** — Reference data from BDH paper (arXiv:2509.26507)

**Note:** These are **locked, labeled files** — not live inference results, but precomputed for consistent demo experience.

### Model Weights (`backend/model_weights/`)
- **`toy_transformer.pt`** — Trained model checkpoint
- **`training_metadata.json`** — Training run metadata (final loss, steps, etc.)

---

## Performance & Optimization

### Optimizations Applied
- **Vectorized BDH update** — Eliminated Python loops, 4x speedup (2000ms → 480ms)
- **CPU-only inference** — No CUDA dependency, portable across environments
- **Precomputed data** — Avoids expensive recomputation during demo

### Profiling Tools Used
- **cProfile** — Python profiler for identifying bottlenecks
- **Custom performance scripts** (`backend/scripts/`)
  - `quick_perf_test.py` — Fast latency sanity check
  - `profile_policies.py` — Detailed cProfile analysis
  - `stress_test.py` — Concurrent requests + edge cases

---

## Testing & Quality Assurance

### Test Coverage
- **72 unit + integration tests** (pytest)
  - Policy correctness tests
  - Endpoint contract tests
  - Edge case validation

### Test Categories
1. **Smoke tests** — Basic functionality (vocab, model forward pass, tasks)
2. **Policy regression tests** — Cache behavior guarantees
3. **Endpoint tests** — API contract and error handling
4. **Stress tests** — Concurrent requests, malformed inputs

### CI/CD
- GitHub Actions workflow for frontend deployment
- Automated build verification

---

## Key Dependencies Rationale

### Why FastAPI?
- Automatic API documentation (OpenAPI/Swagger)
- Fast request validation with Pydantic
- Modern Python async support (though not needed for CPU-bound demo)
- Excellent developer experience

### Why PyTorch (CPU-only)?
- Needed for Transformer implementation and cache manipulation
- Familiar ML framework for hackathon judges
- CPU-only keeps deployment simple (no GPU instance required)

### Why Vite + React?
- Fast dev server with instant HMR
- Modern build tool, simpler than Webpack
- React for component-based UI (familiar to judges)

### Why Python 3.14?
- Latest stable Python (3.14.4 tested)
- All dependencies have prebuilt wheels (no compilation)
- Type hints improve code maintainability

---

## Environment Variables

### Frontend (`.env.development`, `.env.production`)
- `VITE_API_BASE_URL` — Backend API endpoint URL

### Backend
- None required — model weights loaded from local filesystem
- CORS configured for `*` (open for hackathon demo)

---

## Compatibility & Requirements

### Backend
- **Python:** 3.11–3.14
- **OS:** Cross-platform (tested on Windows, should work on Linux/macOS)
- **RAM:** ~2GB for model + inference
- **CPU:** Modern x86_64 (no GPU needed)

### Frontend
- **Node.js:** >=18.0.0
- **Browsers:** Modern ES6+ browsers (Chrome, Firefox, Safari, Edge)

---

## Documentation Files

### Backend
- `SETUP.md` — Installation and local development setup
- `PERFORMANCE_NOTES.md` — Performance measurements and optimization details
- `requirements.txt` — Python dependencies with version notes

### Frontend
- `CONTROLS_SPEC.md` — UI control specifications
- `RESPONSE_TIME_AUDIT.md` — Frontend performance audit
- `wireframe_notes.md` — Design notes

### Root
- `ARCHITECTURE (1).md` — High-level system architecture
- `TECH_STACK.md` — This file

---

## Notable Design Decisions

1. **CPU-only PyTorch** — Keeps deployment simple, no GPU instance needed
2. **Precomputed accuracy curves** — Avoids expensive recomputation, ensures consistent demo
3. **Vectorized cache policies** — Optimized for demo-scale performance (<1s response)
4. **Single-file React components** — Simplicity over complex state management
5. **No database** — Stateless API, all state in request/response
6. **CORS wide-open** — Hackathon demo, not production security

---

## Future Improvements (Out of Scope for Hackathon)

- **GPU support** — 10x+ speedup for model inference
- **Redis caching** — Cache simulation results for identical requests
- **TypeScript** — Better type safety in frontend
- **WebSockets** — Real-time streaming for multi-step simulation
- **Auth/rate limiting** — Production security

---

## License & Attribution

**Model Inspiration:**
- BDH (arXiv:2509.26507) — Conceptual inspiration for fixed-size state policy
- **Critical:** Our implementation is a toy layer, NOT the real BDH architecture

**Dependencies:** All open-source (MIT, BSD, Apache 2.0 licenses)

---

**Last Updated:** Day 5 Performance Pass  
**Project Status:** Ready for hackathon demo deployment
