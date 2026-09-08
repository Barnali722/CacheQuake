"""
Performance measurement script for /simulate endpoint.
Measures actual response times across all four policies and realistic parameter ranges.
"""
import time
import json
import sys
import os
import torch
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.model.toy_transformer import ToyTransformer
from app.cache_policies.full_cache import FullCachePolicy
from app.cache_policies.sliding_window import SlidingWindowPolicy
from app.cache_policies.heavy_hitter import HeavyHitterPolicy
from app.cache_policies.bdh_inspired_state import BDHInspiredState
from app.tasks.needle_haystack import NeedleHaystackTask
from app.simulation.runner import run_episode

# Load the model once
WEIGHTS_DIR = backend_dir / "model_weights"
CKPT_PATH = WEIGHTS_DIR / "toy_transformer.pt"

model = ToyTransformer(
    vocab_size=44,
    d_model=64,
    n_heads=4,
    n_layers=4,
    max_seq_len=512,
)

if CKPT_PATH.exists():
    model.load_state_dict(torch.load(CKPT_PATH, map_location="cpu", weights_only=True))
    print(f"Loaded trained weights from {CKPT_PATH}")
else:
    print("Warning: Using randomly initialized model (no trained weights found)")

model.eval()

def create_policy(policy_name: str, budget: int):
    """Create a policy instance."""
    if policy_name == "full_cache":
        return FullCachePolicy()
    elif policy_name == "sliding_window":
        return SlidingWindowPolicy(window_size=budget, num_sink_tokens=4)
    elif policy_name == "heavy_hitter":
        return HeavyHitterPolicy(budget=budget)
    elif policy_name == "bdh_inspired_state":
        d_head = model.d_model // model.n_heads
        return BDHInspiredState(state_size=budget, d_head=d_head, n_heads=model.n_heads, decay=0.995)
    else:
        raise ValueError(f"Unknown policy: {policy_name}")

def measure_single_run(policy_name: str, seq_length: int, budget: int, warmup: bool = False) -> float:
    """Measure time for a single simulation run."""
    # Create policy and episode
    policy = create_policy(policy_name, budget)
    
    task = NeedleHaystackTask(seed=42)
    episode = task.generate(
        n_facts=8,
        seq_len=seq_length,
        question_target=4
    )
    
    start = time.perf_counter()
    
    result = run_episode(
        model=model,
        policy=policy,
        episode=episode,
        policy_name=policy_name,
        policy_params={}
    )
    
    end = time.perf_counter()
    elapsed_ms = (end - start) * 1000
    
    if not warmup:
        # Verify we got a valid result
        assert len(result.steps) > 0, "No steps in result"
        assert result.final_answer is not None, "No final answer"
    
    return elapsed_ms

def run_performance_suite():
    """Run comprehensive performance measurements."""
    print("=" * 80)
    print("CacheQuake Performance Measurement")
    print("=" * 80)
    print()
    
    policies = ["full_cache", "sliding_window", "heavy_hitter", "bdh_inspired_state"]
    
    # Test scenarios covering realistic frontend usage
    scenarios = [
        # (seq_length, budget, description)
        (32, 16, "Short sequence, half budget"),
        (64, 32, "Medium sequence, half budget"),
        (64, 48, "Medium sequence, 3/4 budget"),
        (128, 32, "Long sequence, quarter budget"),
        (128, 64, "Long sequence, half budget"),
        (128, 96, "Long sequence, 3/4 budget"),
        (256, 64, "Very long sequence, quarter budget"),
        (256, 128, "Very long sequence, half budget"),
    ]
    
    results = {}
    
    for policy in policies:
        print(f"\n{'=' * 80}")
        print(f"Policy: {policy}")
        print(f"{'=' * 80}")
        
        results[policy] = {}
        
        # Warmup run to ensure model is loaded
        print("  Warming up...")
        measure_single_run(policy, 32, 16, warmup=True)
        
        for seq_length, budget, description in scenarios:
            # Skip invalid combinations
            if budget > seq_length:
                continue
            
            # Run 3 times and take median
            times = []
            for _ in range(3):
                elapsed_ms = measure_single_run(policy, seq_length, budget)
                times.append(elapsed_ms)
            
            times.sort()
            median_ms = times[1]  # Middle value
            
            scenario_key = f"seq{seq_length}_budget{budget}"
            results[policy][scenario_key] = {
                "seq_length": seq_length,
                "budget": budget,
                "description": description,
                "median_ms": median_ms,
                "all_runs_ms": times
            }
            
            status = "✓ FAST" if median_ms < 1000 else "⚠ SLOW"
            print(f"  {status} | {description:35} | {median_ms:7.1f} ms")
    
    # Summary statistics
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    for policy in policies:
        all_times = [v["median_ms"] for v in results[policy].values()]
        avg_ms = sum(all_times) / len(all_times)
        max_ms = max(all_times)
        
        status = "✓" if max_ms < 1000 else "⚠"
        print(f"{status} {policy:25} | Avg: {avg_ms:6.1f} ms | Max: {max_ms:6.1f} ms")
    
    # Save detailed results
    output_file = backend_dir / "data" / "performance_results.json"
    output_file.parent.mkdir(exist_ok=True)
    
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\nDetailed results saved to: {output_file}")
    
    # Check if any policy exceeds 1 second
    slow_policies = []
    for policy in policies:
        max_time = max(v["median_ms"] for v in results[policy].values())
        if max_time >= 1000:
            slow_policies.append((policy, max_time))
    
    if slow_policies:
        print("\n⚠ WARNING: The following policies exceed 1 second:")
        for policy, max_time in slow_policies:
            print(f"  - {policy}: {max_time:.1f} ms")
        print("\nConsider profiling and optimization.")
    else:
        print("\n✓ All policies respond in under 1 second across all scenarios.")
    
    return results

if __name__ == "__main__":
    results = run_performance_suite()
