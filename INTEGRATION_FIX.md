# CacheQuake Frontend-Backend Integration Fixes

## Issues Resolved

### 1. Precomputed Data 404 Errors ✅
**Problem**: Frontend showing "Precomputed curve not yet loaded"
**Root Cause**: Backend wasn't serving static files from `data/` directory
**Fix**: Added StaticFiles mount in `backend/app/main.py`:
```python
from fastapi.staticfiles import StaticFiles
_DATA_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "data"))
app.mount("/data", StaticFiles(directory=_DATA_DIR), name="data")
```

### 2. Accuracy Display Logic ✅
**Problem**: UI showing "X 3" vs "5906" with 0% accuracy
**Root Causes**:
1. Comparing full string `model === correct` instead of first character
2. `needle_positions` was empty because `fact_positions` is an object, not array

**Fixes Applied**:
- **simulationStore.jsx line ~216**: Convert object to array
  ```javascript
  const needlePositions = episode.fact_positions && typeof episode.fact_positions === 'object'
    ? Object.values(episode.fact_positions)
    : [];
  ```

- **simulationStore.jsx line ~218**: Simplified array wrapping
  ```javascript
  model_answers: [simulation.final_answer || '?'],
  ground_truth_answers: [simulation.ground_truth || '?'],
  ```

- **AccuracyPanel.jsx line ~212**: Compare first character only
  ```javascript
  const isCorrect = model && correct && model === correct[0];
  ```

- **Added episode metadata to store**:
  ```javascript
  episode_text: episode.text || '',
  episode_token_ids: Array.isArray(episode.token_ids) ? episode.token_ids : [],
  question_start: episode.question_start || 0,
  ```

## How The Model Works

The toy transformer is trained to predict the **first character** of a 4-digit access code:

1. **Episode Structure**: `[FILLER] [FACT: "vault 0 code is 5906"] [FILLER] [QUESTION: "what is vault 0 code?"]`
2. **Model Output**: Single character (e.g., "5")
3. **Ground Truth**: Full code (e.g., "5906")
4. **Correctness**: Model output matches ground_truth[0]

## UI Display Format

```
# | Model Output | Correct Answer
1 | ✓ 5         | 5906
```

- **Green ✓**: First character matches
- **Red ✗**: Wrong prediction

## Files Modified

1. `backend/app/main.py` - Added static files serving
2. `frontend/src/state/simulationStore.jsx` - Fixed data transformation
3. `frontend/src/components/AccuracyPanel.jsx` - Fixed comparison logic

## Testing

Both servers should be running:
- Backend: `http://localhost:8000` 
- Frontend: `http://localhost:5173`

Run simulation and verify:
- ✅ Accuracy curve loads (precomputed data)
- ✅ Model output shows single character
- ✅ Correct answer shows full 4-digit code
- ✅ Accuracy calculated correctly (first char match)
- ✅ Needle positions highlighted in heatmap

## Next Steps

1. Add episode text display above heatmap (optional UX improvement)
2. Remove debug console.logs after verification
3. Test all 4 cache policies (full, sliding_window, heavy_hitter, bdh_inspired_state)
