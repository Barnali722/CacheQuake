"""Quick performance test - minimal version to verify basic timing."""
import time
import sys
import torch
from pathlib import Path

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.model.toy_transformer import ToyTransformer
from app.cache_policies.full_cache import FullCachePolicy
from app.cache_policies.sliding_window import SlidingWindowPolicy
from app.cache_policies.heavy_hitter import HeavyHitterPolicy
from app.cache_policies.bdh_inspired_state import BDHInspiredState
from app.tasks.needle_haystack import NeedleHaystackTask
from app.simulation.runner import run_episode

# Load model
WEIGHTS_DIR = backend_dir / "model_weights"
CKPT_PATH = WEIGHTS_DIR / "toy_transformer.pt"

model = ToyTransformer(vocab_size=44, d_model=64, n_heads=4, n_layers=4, max_seq_len=512)
if CKPT_PATH.exists():
    model.load_state_dict(torch.load(CKPT_PATH, map_location="cpu", weights_only=True))
model.eval()

def test_policy(policy_name, seq_len, budget):
    """Test one policy configuration."""
    # Create policy
    if policy_name == "full_cache":
        policy = FullCachePolicy()
    elif policy_name == "sliding_window":
        policy = SlidingWindowPolicy(window_size=budget, num_sink_tokens=4)
    elif policy_name == "heavy_hitter":
        policy = HeavyHitterPolicy(budget=budget)
    elif policy_name == "bdh_inspired_state":
        d_head = model.d_model // model.n_heads
        policy = BDHInspiredState(state_size=budget, d_head=d_head, n_heads=model.n_heads, decay=0.995)
    
    # Create episode
    task = NeedleHaystackTask(seed=42)
    episode = task.generate(n_facts=8, seq_len=seq_len, question_target=4)
    
    # Time the execution
    start = time.perf_counter()
    result = run_episode(model=model, policy=policy, episode=episode, policy_name=policy_name, policy_params={})
    elapsed_ms = (time.perf_counter() - start) * 1000
    
    return elapsed_ms, len(result.steps)

# Test each policy with a few sizes
print("Quick Performance Test")
print("=" * 60)

configs = [
    ("full_cache", 64, 64),
    ("full_cache", 128, 128),
    ("sliding_window", 64, 32),
    ("sliding_window", 128, 64),
    ("heavy_hitter", 64, 32),
    ("heavy_hitter", 128, 64),
    ("bdh_inspired_state", 64, 32),
    ("bdh_inspired_state", 128, 64),
]

for policy_name, seq_len, budget in configs:
    try:
        elapsed, steps = test_policy(policy_name, seq_len, budget)
        status = "OK" if elapsed < 1000 else "SLOW"
        print(f"{status:4} | {policy_name:20} | seq={seq_len:3}, budget={budget:3} | {elapsed:7.1f} ms | {steps} steps")
    except Exception as e:
        print(f"FAIL | {policy_name:20} | seq={seq_len:3}, budget={budget:3} | ERROR: {e}")

print("=" * 60)
print("Done")
