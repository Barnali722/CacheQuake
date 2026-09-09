# API Mapping — Frontend ↔ Backend

This document describes how the frontend transforms data between its internal state and the backend API.

---

## POST /simulate Request Mapping

### Frontend Control State → Backend Request

| Frontend Field       | Backend Field    | Transformation                              |
|---------------------|------------------|---------------------------------------------|
| `cachePolicy`       | `policy`         | Map: `"full"` → `"full_cache"`, etc.       |
| `budgetSize`        | `budget`         | Direct pass-through                         |
| `sequenceLength`    | `seq_len`        | Direct pass-through                         |
| `needleCount`       | `n_facts`        | Renamed field                               |
| *(not in controls)* | `question_target`| Fixed value: `0`                            |
| *(not in controls)* | `seed`           | Fixed value: `42`                           |

**Policy Name Mapping:**
```javascript
{
  'full': 'full_cache',
  'sliding_window': 'sliding_window',
  'heavy_hitter': 'heavy_hitter',
  'bdh_recurrent': 'bdh_inspired_state',
}
```

---

## POST /simulate Response Mapping

### Backend Response → Frontend State

**Backend returns:**
```json
{
  "episode": {
    "text": "...",
    "token_ids": [1, 2, 3, ...],
    "fact_positions": [12, 45, 78],
    "question_start": 150,
    "answer": "Paris"
  },
  "simulation": {
    "policy": "full_cache",
    "policy_params": {},
    "steps": [
      {
        "step": 0,
        "token_id": 1,
        "token_char": "a",
        "visible_token_indices": [0],
        "cache_size_tokens": 1,
        "cache_size_bytes": 2048
      },
      ...
    ],
    "final_answer": "Paris",
    "ground_truth": "Paris",
    "correct": true,
    "policy_info": {}
  }
}
```

**Frontend expects:**
```json
{
  "cache_size_tokens": 128,
  "full_cache_baseline_tokens": 128,
  "alive_token_indices": [0, 1, 2, ..., 127],
  "model_answers": ["Paris"],
  "ground_truth_answers": ["Paris"],
  "accuracy_score": 1.0,
  "cache_size_history": [1, 2, 3, ..., 128],
  "baseline_history": [1, 2, 3, ..., 128],
  "needle_positions": [12, 45, 78]
}
```

### Transformation Logic

```javascript
const { episode, simulation } = response;
const steps = simulation.steps || [];

const transformedResult = {
  // Final cache size from last step
  cache_size_tokens: steps.length > 0 
    ? steps[steps.length - 1].cache_size_tokens 
    : 0,
  
  // Baseline = total sequence length
  full_cache_baseline_tokens: steps.length,
  
  // Tokens currently in cache (from last step)
  alive_token_indices: steps.length > 0 
    ? steps[steps.length - 1].visible_token_indices 
    : [],
  
  // Model prediction (single answer)
  model_answers: [simulation.final_answer],
  
  // Ground truth (single answer)
  ground_truth_answers: [simulation.ground_truth],
  
  // Binary accuracy (correct or not)
  accuracy_score: simulation.correct ? 1.0 : 0.0,
  
  // Cache size at each step (for chart)
  cache_size_history: steps.map(s => s.cache_size_tokens),
  
  // Full-cache baseline growth (for chart)
  baseline_history: steps.map((_, i) => i + 1),
  
  // Where needles were placed
  needle_positions: episode.fact_positions || [],
};
```

---

## Key Differences

### 1. Nested vs. Flat Structure
- **Backend:** Nested under `episode` and `simulation`
- **Frontend:** Flat object for easier component access

### 2. Granular vs. Summary Data
- **Backend:** Provides per-step data in `steps[]` array
- **Frontend:** Extracts final state + history arrays for visualization

### 3. Multi-needle Support
- **Backend:** Can handle multiple needles (n_facts parameter)
- **Frontend:** Currently expects single answer in arrays
  - *Note: This is a simplification; future versions may support multiple needles fully*

---

## Why This Mapping Exists

The frontend and backend were developed with different data models:

1. **Backend** is step-oriented:
   - Records every token generation step
   - Provides full trace for detailed analysis
   - Designed for research/debugging

2. **Frontend** is visualization-oriented:
   - Needs final state + time series for charts
   - Expects simplified accuracy metrics
   - Optimized for learner UI

Rather than changing one side to match the other (breaking existing code), we transform at the boundary in `simulationStore.jsx`.

---

## Future Improvements

1. **Backend could provide summary endpoint:**
   ```
   POST /simulate?summary=true
   ```
   Returns pre-aggregated data in frontend format.

2. **Frontend could work with step data directly:**
   - Store full step trace
   - Compute derived metrics in components
   - Allows scrubbing through simulation timeline

3. **Unified schema:**
   - Define shared TypeScript types
   - Backend validates output against schema
   - Frontend validates input against schema

---

**Last Updated:** Day 5 Integration Fix  
**File:** `frontend/src/state/simulationStore.jsx` (lines ~190-210)
