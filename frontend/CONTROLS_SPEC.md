# CONTROLS_SPEC.md — "Memory Under Pressure"
**Frontend/Interaction Engineer · Day 1 Deliverable · DataForge 2026**

> Every control maps to exactly one backend variable. Every readout is specified as a live value beside a baseline/ground-truth value. No decorative controls exist in this spec.

---

## Section 1: Controls

---

### 1.1 Cache Policy Selector

| Field | Value |
|---|---|
| **Variable name** | `cachePolicy` |
| **Type** | `enum` (string) |
| **Allowed values** | `"full"` \| `"sliding_window"` \| `"heavy_hitter"` \| `"bdh_recurrent"` |
| **Default** | `"full"` |
| **UI element** | Segmented button group (4 tabs) |
| **Backend mapping** | Maps directly to the `policy` field in the `/simulate` request body (see `backend/app/api/schemas.py`). The backend routes this to one of: `full_cache.py`, `sliding_window.py`, `heavy_hitter.py`, or `bdh_inspired_state.py` in `cache_policies/`. |
| **PrecomputedBadge?** | No — policy selection triggers a live simulation run. |
| **Notes** | When `cachePolicy === "full"`, the `budgetSize` control must be **disabled** (greyed out). When `cachePolicy === "bdh_recurrent"`, the BDH Module explainer panel should expand inline. |

---

### 1.2 Budget Size

| Field | Value |
|---|---|
| **Variable name** | `budgetSize` |
| **Type** | `integer` |
| **Allowed range** | `8` – `512` (inclusive), step `8` |
| **Default** | `64` |
| **UI element** | Horizontal slider + numeric readout label |
| **Backend mapping** | Maps to `budget` in the `/simulate` request body. Passed as-is to `sliding_window.py` (window size = `budget`), `heavy_hitter.py` (max survivors = `budget`), and `bdh_inspired_state.py` (fixed state size = `budget`). Full cache policy ignores this field entirely. |
| **PrecomputedBadge?** | No — live parameter. **Exception:** the accuracy-vs-budget sweep curve shown beside the live point IS precomputed (see Readout 2.3 below). |
| **Notes** | Disabled (opacity 0.4, pointer-events none) when `cachePolicy === "full"`. Label must show current value in tokens, e.g. `"64 tokens"`. |

---

### 1.3 Sequence Length

| Field | Value |
|---|---|
| **Variable name** | `sequenceLength` |
| **Type** | `integer` |
| **Allowed range** | `32` – `512` (inclusive), step `16` |
| **Default** | `128` |
| **UI element** | Horizontal slider + numeric readout label |
| **Backend mapping** | Maps to `seq_len` in the `/simulate` request body. Passed to `needle_haystack.py` which generates a synthetic sequence of exactly this length containing `needleCount` embedded facts. |
| **PrecomputedBadge?** | No — live parameter. |
| **Notes** | Increasing this visibly grows the memory footprint under `"full"` policy — this is the primary demonstration of the linear-growth claim. |

---

### 1.4 Needle Count

| Field | Value |
|---|---|
| **Variable name** | `needleCount` |
| **Type** | `integer` |
| **Allowed range** | `1` – `5` (inclusive), step `1` |
| **Default** | `2` |
| **UI element** | Stepper buttons (minus / plus) with numeric label |
| **Backend mapping** | Maps to `num_needles` in the `/simulate` request body. Passed to `needle_haystack.py` to embed this many retrievable facts into the generated sequence. |
| **PrecomputedBadge?** | No — live parameter. |
| **Notes** | Kept small (max 5) so all needles can be checked individually in the Accuracy Panel. |

---

## Section 2: Readouts

All readouts show a **live value beside a baseline/ground-truth value**. No single-number readouts exist.

---

### 2.1 Memory Footprint Readout (MemoryChart)

| Field | Value |
|---|---|
| **Live value** | `memoryUsed` — current token count retained in cache (integer, in tokens). Computed per-step by the active policy. Source: `/simulate` response, field `cache_size_tokens`. |
| **Baseline value** | `memoryBaseline` — what Full Cache would use for the same `sequenceLength`: `sequenceLength x num_layers x num_heads x head_dim_bytes`. Source: `/simulate` response, field `full_cache_baseline_tokens`. Always shown as a flat horizontal reference line. |
| **Comparison being made** | Ratio: `memoryUsed / memoryBaseline`. Chart shows both values on the same Y-axis so reduction is immediately visible. |
| **Chart type** | Line chart (X = generation step, Y = tokens in cache). Two lines: live policy (colored) vs. full-cache baseline (dashed grey). |
| **PrecomputedBadge?** | **No** — both values come from the live `/simulate` call. |
| **Label** | "Live — computed this run" shown as a small inline tag. |

---

### 2.2 Needle Retrieval Accuracy Readout (AccuracyPanel)

| Field | Value |
|---|---|
| **Live value** | `modelAnswer` — the toy model's answer to each needle question, extracted from the generation output. Source: `/simulate` response, field `model_answers[]`. |
| **Ground-truth value** | `correctAnswer` — the correct answer embedded in the needle sequence by `needle_haystack.py`. Source: `/simulate` response, field `ground_truth_answers[]`. |
| **Comparison being made** | Exact match per needle: `modelAnswer[i] === correctAnswer[i]`. Displayed as: correct answers shown in green, wrong answers shown in red, side-by-side with the model's actual output string. |
| **PrecomputedBadge?** | **No** — both values come from the live `/simulate` call. |
| **Label** | "Model output" vs. "Correct answer" column headers. |

---

### 2.3 Accuracy-vs-Budget Curve (budget sweep overlay in AccuracyPanel)

| Field | Value |
|---|---|
| **Live value** | The single point `(budgetSize, accuracyScore)` from the current live run. Source: `/simulate` response. |
| **Baseline value** | The precomputed accuracy curve `accuracy_vs_budget.json` — a sweep over all budget values at a fixed `sequenceLength`. Source: `data/precomputed/accuracy_vs_budget.json`. |
| **Comparison being made** | "Where does my current budget sit on the trade-off curve?" — live point plotted atop the precomputed curve so the learner sees the full trade-off at a glance. |
| **PrecomputedBadge?** | **YES** — the curve (not the current point) is precomputed. `PrecomputedBadge` must render beside the curve legend with text: "Accuracy curve — precomputed sweep, not this run." |

---

### 2.4 Cache Heat-Map (CacheHeatmap)

| Field | Value |
|---|---|
| **Live value** | `aliveTokenIndices` — which token positions are still present in the KV cache after the last generation step. Source: `/simulate` response, field `alive_token_indices[]`. |
| **Baseline value** | Implicit baseline is "all tokens alive" (Full Cache state). Tokens NOT in `aliveTokenIndices` are rendered as dim/grey; tokens that ARE alive are rendered as bright/colored. The full-cache baseline is shown as a reference row of all-bright cells. |
| **Comparison being made** | Visual: alive tokens (current policy) vs. all-alive (full cache). Makes the "what did you lose?" question immediately perceptible. |
| **PrecomputedBadge?** | **No** — `aliveTokenIndices` is live per-step. |
| **Label** | "Live cache state" below the heat-map grid. |

---

### 2.5 BDH Comparison Panel (BDHModule)

| Field | Value |
|---|---|
| **Live value** | Our toy simulator's accuracy and memory stats for `bdh_recurrent` policy at the current `budgetSize` and `sequenceLength`. Source: `/simulate` response (same fields as 2.1 and 2.2). |
| **Baseline/Published value** | BDH paper's published long-context performance claims. Source: `data/precomputed/bdh_published_claims.json`, sourced from `research/papers/dragon_hatchling_bdh.md` (arXiv:2509.26507). |
| **Comparison being made** | Qualitative side-by-side: "What our toy shows" vs. "What the BDH paper reports (at full scale)." NOT a direct numerical comparison — the two models differ in scale by orders of magnitude. |
| **PrecomputedBadge?** | **YES** — published claims panel must carry `PrecomputedBadge` with text: "Published result (arXiv:2509.26507) — not reproduced by our team." This is mandatory per the honesty rubric. |

---

## Section 3: PrecomputedBadge Inventory

| Location | Badge text | Why |
|---|---|---|
| Accuracy-vs-budget curve overlay (Section 2.3) | "Precomputed sweep — not this run" | Curve is a pre-run sweep over many budgets, not computed live |
| BDH comparison panel (Section 2.5) | "Published result (arXiv:2509.26507) — not reproduced by our team" | Numbers come from the BDH paper, not our simulator |

All other readouts are live. No further precomputed elements exist in Day 1 scope.

---

## Section 4: Controls Pending Backend Sign-off

None at this time. All four controls (`cachePolicy`, `budgetSize`, `sequenceLength`, `needleCount`) have confirmed mappings to `/simulate` request fields per `ARCHITECTURE.md Section 3`.

---

## Section 5: Variable to API Mapping Summary

```
POST /simulate
{
  "policy":       cachePolicy,      // "full" | "sliding_window" | "heavy_hitter" | "bdh_recurrent"
  "budget":       budgetSize,       // integer 8-512 (ignored by backend when policy="full")
  "seq_len":      sequenceLength,   // integer 32-512
  "num_needles":  needleCount       // integer 1-5
}

Response (per step):
{
  "cache_size_tokens":          number,   -> memoryUsed (Readout 2.1 live)
  "full_cache_baseline_tokens": number,   -> memoryBaseline (Readout 2.1 baseline)
  "alive_token_indices":        number[], -> aliveTokenIndices (Readout 2.4)
  "model_answers":              string[], -> modelAnswer[] (Readout 2.2 live)
  "ground_truth_answers":       string[], -> correctAnswer[] (Readout 2.2 ground truth)
  "accuracy_score":             number    -> live point for Readout 2.3
}
```

---

*Produced by Agent 1 — Spec Agent.*
*Companion documents: `ARCHITECTURE.md`, `PRD_KV_Cache_Explainer.md`, `wireframe_notes.md`*
