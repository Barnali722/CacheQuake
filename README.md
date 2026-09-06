# Memory Under Pressure — KV Caching Explainer
**DataForge 2026 · IIT Kharagpur · Pathway × Rime Track**

> "A Transformer's KV cache grows linearly with every token it has ever seen because it stores an exact copy of the past; eviction and compression trade that exactness for a bounded budget, and architectures like BDH remove the growth altogether by replacing the cache with a fixed-size associative state that overwrites itself instead of appending."

---

## 🚀 Quick Start

```bash
# Frontend (React + Vite)
cd frontend
npm install
npm run dev
# → http://localhost:5173

# Backend (FastAPI — optional; app runs in demo mode without it)
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**Live demo:** https://barnali722.github.io/CacheQuake/

---

## 📂 Project Structure

```
CacheQuake/
├── frontend/         React + Vite interactive explainer
│   ├── src/
│   │   ├── components/   UI components (CacheHeatmap, MemoryChart, BDHModule…)
│   │   ├── state/        simulationStore.jsx — global state + API wiring
│   │   └── api/          client.js — /simulate, /step endpoints
│   └── public/
├── backend/          FastAPI simulation engine (Python)
├── docs/             one_page_summary.md, blog.md
└── ARCHITECTURE.md   System design & component contracts
```

---

## 🔬 Technical References & Citations

All technical claims in the UI are traceable to the following primary sources:

| Claim | Source | DOI / URL |
|---|---|---|
| KV cache grows O(n) with sequence length | Vaswani et al., "Attention Is All You Need" (2017) | arXiv:1706.03762 |
| Sliding Window / sink-token eviction | Xiao et al., "Efficient Streaming Language Models with Attention Sinks" (StreamingLLM, 2023) | arXiv:2309.17453 |
| Heavy-Hitter Oracle (H2O) attention-score eviction | Zhang et al., "H2O: Heavy-Hitter Oracle for Efficient Generative Inference" (2023) | arXiv:2306.14048 |
| SnapKV / Quest / KVzip compression policies | See PRD_KV_Cache_Explainer.md §References for full list | — |
| BDH fixed-size synaptic state (`W ← W + k·vᵀ`), O(1) memory, Hebbian update rule | Yıldız et al., "Beyond Dense-Hop: Associative Memory Networks" (2025) | arXiv:2509.26507 |
| BDH-CQ variant (limited applicability to standard KV cache replacement) | Same paper, §5 | arXiv:2509.26507 |

> **Note on BDH-CQ:** BDH-CQ extends BDH with a contrastive-query mechanism. Its relevance to standard attention KV caching is limited — this project teaches the core BDH memory model, not BDH-CQ specifically.

---

## 🏷️ Licenses & Credits

| Asset | Source | License |
|---|---|---|
| React | Meta / React team | MIT |
| Vite | Evan You / Vite contributors | MIT |
| FastAPI | Sebastián Ramírez | MIT |
| Inter font | Rasmus Andersson / Google Fonts | SIL OFL 1.1 |
| `@vitejs/plugin-react` | Vite team | MIT |
| Project source code | This team (Barnali722/CacheQuake) | MIT — see [LICENSE](LICENSE) |
| Research papers cited | Respective authors | All cited works used for educational reference only; no figures reproduced without permission |

---

## 🎓 Learning Objectives

After completing the guided walkthrough a learner should be able to:

1. Explain why a Transformer's KV cache grows linearly with sequence length
2. Describe what Sliding Window and Heavy Hitter eviction each trade away (early context / attention-scored tokens)
3. Explain how BDH replaces the cache with a fixed-size synaptic state that overwrites instead of appending
4. Predict the effect of changing the budget slider on needle retrieval accuracy

---

## 📋 Rubric Compliance Notes

- **Live vs. Precomputed:** Every on-screen readout is labeled. Live values come from `/simulate`. The accuracy-vs-budget curve is precomputed (labeled with `PrecomputedBadge`). BDH published claims are labeled "Published (arXiv:2509.26507) — not reproduced by our team."
- **Demo Mode:** When the backend is unreachable, the app runs deterministic mock data. A "DEMO MODE" label is shown next to the LIVE badge in this state.
- **ComprehensionCheck:** Placeholder — requires Research/Content lead to finalize questions (see Flagged for Human Decision in audit report).
