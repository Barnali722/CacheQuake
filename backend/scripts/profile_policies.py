"""Profile the slow policies to identify bottlenecks."""
import cProfile
import pstats
import io
import sys
import torch
from pathlib import Path

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.model.toy_transformer import ToyTransformer
from app.cache_policies.heavy_hitter import HeavyHitterPolicy
from app.cache_policies.bdh_inspired_state import BDHInspiredState
from app.cache_policies.sliding_window import SlidingWindowPolicy
from app.tasks.needle_haystack import NeedleHaystackTask
from app.simulation.runner import run_episode

# Load model
WEIGHTS_DIR = backend_dir / "model_weights"
CKPT_PATH = WEIGHTS_DIR / "toy_transformer.pt"

model = ToyTransformer(vocab_size=44, d_model=64, n_heads=4, n_layers=4, max_seq_len=512)
if CKPT_PATH.exists():
    model.load_state_dict(torch.load(CKPT_PATH, map_location="cpu", weights_only=True))
model.eval()

def profile_policy(policy_name, policy, seq_len=128):
    """Profile a single policy execution."""
    task = NeedleHaystackTask(seed=42)
    episode = task.generate(n_facts=8, seq_len=seq_len, question_target=4)
    
    # Profile the execution
    profiler = cProfile.Profile()
    profiler.enable()
    
    result = run_episode(model=model, policy=policy, episode=episode, policy_name=policy_name, policy_params={})
    
    profiler.disable()
    
    # Print stats
    s = io.StringIO()
    ps = pstats.Stats(profiler, stream=s)
    ps.strip_dirs()
    ps.sort_stats('cumulative')
    
    print(f"\n{'='*70}")
    print(f"Profile for {policy_name} (seq_len={seq_len})")
    print(f"{'='*70}")
    ps.print_stats(20)  # Top 20 functions
    print(s.getvalue())

# Profile each slow policy
print("Profiling slow policies...")

# Heavy hitter
d_head = model.d_model // model.n_heads
policy = HeavyHitterPolicy(budget=64)
profile_policy("heavy_hitter", policy, seq_len=128)

# BDH inspired state
policy = BDHInspiredState(state_size=64, d_head=d_head, n_heads=model.n_heads, decay=0.995)
profile_policy("bdh_inspired_state", policy, seq_len=128)

# Sliding window
policy = SlidingWindowPolicy(window_size=64, num_sink_tokens=4)
profile_policy("sliding_window", policy, seq_len=128)

print("\nProfiling complete.")
