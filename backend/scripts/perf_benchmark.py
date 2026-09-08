"""
backend/scripts/perf_benchmark.py

Measures /simulate wall-clock latency for all four cache policies across
a range of seq_len and budget values.  Run from backend/:

    .venv_verify\Scripts\python.exe scripts/perf_benchmark.py

Outputs a markdown-formatted table suitable for copy-paste into
PERFORMANCE_NOTES.md.
"""
import sys, os, time, statistics
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import torch
from app.model.toy_transformer import ToyTransformer
from app.model.vocab import VOCAB_SIZE
from app.tasks.needle_haystack import NeedleHaystackTask
from app.cache_policies.full_cache      import FullCachePolicy
from app.cache_policies.sliding_window  import SlidingWindowPolicy
from app.cache_policies.heavy_hitter    import HeavyHitterPolicy
from app.cache_policies.bdh_inspired_state import BDHInspiredState
from app.simulation.runner import run_episode

CKPT = os.path.join(os.path.dirname(__file__), "..", "model_weights", "toy_transformer.pt")
N_REPS   = 5     # repeat each (policy, seq_len, budget) N times; report median
SEED_BASE = 200  # different from train (42) and eval (100) seeds

# ── Load model ───────────────────────────────────────────────────────────────
model = ToyTransformer(vocab_size=VOCAB_SIZE, d_model=64, n_heads=4,
                       n_layers=4, max_seq_len=512)
if os.path.exists(CKPT):
    model.load_state_dict(torch.load(CKPT, map_location="cpu", weights_only=True))
    print(f"Loaded trained weights from {CKPT}")
else:
    print("WARNING: no checkpoint found, using random weights")
model.eval()

def time_policy(policy_fn, seq_len, budget, n_reps=N_REPS):
    """Return (median_ms, min_ms, max_ms) over n_reps runs."""
    times = []
    for rep in range(n_reps):
        task = NeedleHaystackTask(seed=SEED_BASE + rep)
        ep   = task.generate(n_facts=3, seq_len=seq_len, question_target=0)
        policy = policy_fn()
        t0 = time.perf_counter()
        run_episode(model, policy, ep, "bench", {})
        times.append((time.perf_counter() - t0) * 1000)
    return statistics.median(times), min(times), max(times)

# ── Benchmark matrix ─────────────────────────────────────────────────────────
configs = [
    # (label, policy_fn, seq_len, budget_label)
    # full_cache — no budget
    ("full_cache",           lambda: FullCachePolicy(),                        80,  "inf"),
    ("full_cache",           lambda: FullCachePolicy(),                        120, "inf"),
    ("full_cache",           lambda: FullCachePolicy(),                        200, "inf"),
    # sliding_window
    ("sliding_window",       lambda: SlidingWindowPolicy(8,  num_sink_tokens=2), 120, 8),
    ("sliding_window",       lambda: SlidingWindowPolicy(32, num_sink_tokens=2), 120, 32),
    ("sliding_window",       lambda: SlidingWindowPolicy(64, num_sink_tokens=2), 120, 64),
    ("sliding_window",       lambda: SlidingWindowPolicy(96, num_sink_tokens=2), 200, 96),
    # heavy_hitter
    ("heavy_hitter",         lambda: HeavyHitterPolicy(budget=8),               120, 8),
    ("heavy_hitter",         lambda: HeavyHitterPolicy(budget=32),              120, 32),
    ("heavy_hitter",         lambda: HeavyHitterPolicy(budget=64),              120, 64),
    ("heavy_hitter",         lambda: HeavyHitterPolicy(budget=96),              200, 96),
    # bdh_inspired_state
    ("bdh_inspired_state",   lambda: BDHInspiredState(state_size=8),            120, 8),
    ("bdh_inspired_state",   lambda: BDHInspiredState(state_size=32),           120, 32),
    ("bdh_inspired_state",   lambda: BDHInspiredState(state_size=64),           120, 64),
    ("bdh_inspired_state",   lambda: BDHInspiredState(state_size=96),           200, 96),
]

print(f"\nBenchmarking {len(configs)} configs × {N_REPS} reps each …\n")
print(f"{'Policy':<22} {'seq_len':>8} {'budget':>8} {'median_ms':>10} {'min_ms':>8} {'max_ms':>8}")
print("-" * 68)

results = []
for (label, policy_fn, seq_len, budget) in configs:
    med, mn, mx = time_policy(policy_fn, seq_len, budget)
    print(f"{label:<22} {seq_len:>8} {str(budget):>8} {med:>10.1f} {mn:>8.1f} {mx:>8.1f}")
    results.append((label, seq_len, budget, med, mn, mx))

print()
slowest = max(results, key=lambda r: r[3])
print(f"Slowest: {slowest[0]} seq={slowest[1]} budget={slowest[2]}  → {slowest[3]:.1f} ms median")
threshold = 1000.0
over = [r for r in results if r[3] > threshold]
if over:
    print(f"\nWARNING: {len(over)} config(s) exceed {threshold:.0f} ms threshold:")
    for r in over:
        print(f"  {r[0]} seq={r[1]} budget={r[2]} → {r[3]:.1f} ms")
else:
    print(f"\nAll configs under {threshold:.0f} ms. Target met.")

# ── Markdown table for PERFORMANCE_NOTES.md ──────────────────────────────────
print("\n\n=== Markdown table (copy to PERFORMANCE_NOTES.md) ===\n")
print("| Policy | seq_len | budget | median_ms | min_ms | max_ms | Under 1 s? |")
print("|--------|---------|--------|-----------|--------|--------|------------|")
for (label, seq_len, budget, med, mn, mx) in results:
    ok = "✅" if med < 1000 else "❌"
    print(f"| `{label}` | {seq_len} | {budget} | {med:.1f} | {mn:.1f} | {mx:.1f} | {ok} |")
