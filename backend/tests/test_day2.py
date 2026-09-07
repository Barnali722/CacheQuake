# backend/tests/test_day2.py
"""
Day 2 regression tests for CacheQuake.

What these tests verify:
    1. End-to-end forward pass: real K/V tensors from a real episode sequence.
    2. full_cache never drops any token — visible_token_indices grows monotonically.
    3. sliding_window keeps exactly sink + recent tokens and drops the right rows.
    4. sliding_window with num_sink_tokens=0 behaves as a naive sliding window.
    5. /simulate returns 200 and a well-formed response for full_cache.
    6. /simulate returns 200 and a well-formed response for sliding_window.
    7. /simulate returns 400 for an unknown policy.
    8. /simulate returns 400 for question_target >= n_facts.
    9. Cache mask is genuinely wired in: evicted tokens produce −∞ in attention.

Run from backend/:
    pytest tests/test_day2.py -v
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
import torch


# ===========================================================================
# 1. End-to-end forward pass on a real episode sequence
# ===========================================================================

class TestEndToEndForwardPass:
    """Confirms the forward pass produces real, non-placeholder K/V tensors."""

    @pytest.fixture(scope="class")
    @classmethod
    def model_and_episode(cls):
        from app.model.toy_transformer import ToyTransformer
        from app.tasks.needle_haystack import NeedleHaystackTask
        m = ToyTransformer(vocab_size=44, d_model=64, n_heads=4,
                           n_layers=4, max_seq_len=512)
        m.eval()
        task = NeedleHaystackTask(seed=0)
        ep = task.generate(n_facts=2, seq_len=80, question_target=0)
        return m, ep

    def test_logits_are_not_zeros(self, model_and_episode):
        """Logits should vary — a zero-output would indicate a broken forward pass."""
        model, ep = model_and_episode
        ids = torch.tensor([ep.token_ids[:8]], dtype=torch.long)
        with torch.no_grad():
            logits, _ = model(ids)
        # Check that not all logits are zero or constant
        assert logits.std().item() > 0.0, \
            "All logits are identical — forward pass may be broken"

    def test_k_v_are_real_computation(self, model_and_episode):
        """K and V must differ between layers — they are genuinely computed."""
        model, ep = model_and_episode
        ids = torch.tensor([ep.token_ids[:8]], dtype=torch.long)
        with torch.no_grad():
            _, present_caches = model(ids)
        k0, v0 = present_caches[0]
        k3, v3 = present_caches[3]
        # Different layers should produce different K tensors
        assert not torch.allclose(k0, k3), \
            "Layer 0 and Layer 3 K tensors are identical — layers may be sharing state"

    def test_two_different_inputs_give_different_kv(self, model_and_episode):
        """Different input tokens must produce different K/V vectors."""
        model, ep = model_and_episode
        ids_a = torch.tensor([[ep.token_ids[0]]], dtype=torch.long)
        ids_b = torch.tensor([[ep.token_ids[1]]], dtype=torch.long)
        with torch.no_grad():
            _, caches_a = model(ids_a)
            _, caches_b = model(ids_b)
        ka, _ = caches_a[0]
        kb, _ = caches_b[0]
        assert not torch.allclose(ka, kb), \
            "Different input tokens produced identical K vectors"

    def test_cache_mask_affects_output(self, model_and_episode):
        """Setting cache_mask to all-False for past tokens must change the output."""
        model, ep = model_and_episode
        B, T_prefill = 1, 6

        ids_pre = torch.tensor([ep.token_ids[:T_prefill]], dtype=torch.long)
        ids_cur = torch.tensor([[ep.token_ids[T_prefill]]], dtype=torch.long)

        with torch.no_grad():
            _, past_caches = model(ids_pre)

        # Compute output with all past tokens visible (all-True mask)
        mask_visible = torch.ones(B, T_prefill, dtype=torch.bool)
        with torch.no_grad():
            logits_visible, _ = model(ids_cur,
                                       past_caches=[(k, v) for k, v in past_caches],
                                       cache_masks=[mask_visible] * 4)

        # Compute output with all past tokens evicted (all-False mask)
        mask_evicted = torch.zeros(B, T_prefill, dtype=torch.bool)
        with torch.no_grad():
            logits_evicted, _ = model(ids_cur,
                                       past_caches=[(k, v) for k, v in past_caches],
                                       cache_masks=[mask_evicted] * 4)

        # The outputs must differ — the mask is genuinely controlling attention
        assert not torch.allclose(logits_visible, logits_evicted), (
            "cache_mask=all-True and cache_mask=all-False produced identical logits. "
            "The mask is not actually wired into the attention computation."
        )


# ===========================================================================
# 2. full_cache policy regression
# ===========================================================================

class TestFullCacheRegression:
    """full_cache must accumulate every token and never drop any."""

    def _run_policy(self, n_steps: int):
        """Run the full-cache policy for n_steps and return per-step T_kept."""
        from app.cache_policies.full_cache import FullCachePolicy
        policy = FullCachePolicy()
        B, H, d_head = 1, 4, 16
        results = []
        past_cache = None
        for step in range(n_steps):
            k = torch.randn(B, H, 1, d_head)
            v = torch.randn(B, H, 1, d_head)
            K_stored, V_stored, mask = policy.update(
                step=step, layer_idx=0, k=k, v=v, past_cache=past_cache
            )
            past_cache = (K_stored, V_stored)
            results.append(K_stored.shape[2])
        return results, policy

    def test_monotonically_growing(self):
        sizes, _ = self._run_policy(10)
        for i in range(1, len(sizes)):
            assert sizes[i] == sizes[i - 1] + 1, \
                f"Step {i}: cache size went from {sizes[i-1]} to {sizes[i]} — expected +1"

    def test_never_evicts(self):
        sizes, policy = self._run_policy(50)
        assert policy.memory_tokens_used() == 50
        assert sizes[-1] == 50

    def test_mask_always_all_true(self):
        """Every mask returned must be all-True — full cache never masks anything out."""
        from app.cache_policies.full_cache import FullCachePolicy
        policy = FullCachePolicy()
        B, H, d_head = 1, 4, 16
        past = None
        for step in range(20):
            k = torch.randn(B, H, 1, d_head)
            v = torch.randn(B, H, 1, d_head)
            K_stored, V_stored, mask = policy.update(step, 0, k, v, past)
            past = (K_stored, V_stored)
            assert mask.all(), f"Step {step}: mask has False entries — full_cache should never evict"


# ===========================================================================
# 3. sliding_window policy regression
# ===========================================================================

class TestSlidingWindowRegression:

    def _run_policy(self, n_steps, window_size, num_sink_tokens):
        """Run sliding_window for n_steps; return per-step T_kept and the policy."""
        from app.cache_policies.sliding_window import SlidingWindowPolicy
        policy = SlidingWindowPolicy(window_size=window_size,
                                     num_sink_tokens=num_sink_tokens)
        B, H, d_head = 1, 4, 16
        results = []
        past = None
        for step in range(n_steps):
            k = torch.randn(B, H, 1, d_head)
            v = torch.randn(B, H, 1, d_head)
            K_stored, V_stored, mask = policy.update(step, 0, k, v, past)
            past = (K_stored, V_stored)
            results.append(K_stored.shape[2])
        return results, policy

    def test_grows_until_budget_then_stays_constant(self):
        W, S = 8, 2
        sizes, _ = self._run_policy(n_steps=30, window_size=W, num_sink_tokens=S)
        budget = W + S
        # Should grow for the first `budget` steps, then stay flat
        for i, sz in enumerate(sizes):
            expected = min(i + 1, budget)
            assert sz == expected, \
                f"Step {i}: expected T_kept={expected}, got {sz}"

    def test_sink_tokens_preserved(self):
        """After many steps, verify the stored K vectors include the earliest ones."""
        from app.cache_policies.sliding_window import SlidingWindowPolicy
        W, S = 4, 2
        policy = SlidingWindowPolicy(window_size=W, num_sink_tokens=S)
        B, H, d_head = 1, 4, 16

        # Create distinct K vectors so we can track them
        all_k = [torch.full((B, H, 1, d_head), float(i)) for i in range(20)]

        past = None
        for step in range(20):
            K_stored, V_stored, _ = policy.update(step, 0, all_k[step],
                                                    all_k[step], past)
            past = (K_stored, V_stored)

        # After 20 steps with S=2 sinks, the first two rows of K_stored
        # must still be the original token 0 and token 1 values.
        assert torch.allclose(K_stored[0, 0, 0, :],
                               torch.full((d_head,), 0.0)), \
            "Sink token 0 was evicted — sinks must be preserved forever"
        assert torch.allclose(K_stored[0, 0, 1, :],
                               torch.full((d_head,), 1.0)), \
            "Sink token 1 was evicted — sinks must be preserved forever"

    def test_window_tokens_are_most_recent(self):
        """Tokens just after the sink region must be the most recent W tokens."""
        from app.cache_policies.sliding_window import SlidingWindowPolicy
        W, S = 4, 2
        policy = SlidingWindowPolicy(window_size=W, num_sink_tokens=S)
        B, H, d_head = 1, 4, 16

        all_k = [torch.full((B, H, 1, d_head), float(i)) for i in range(20)]
        past = None
        for step in range(20):
            K_stored, _, _ = policy.update(step, 0, all_k[step], all_k[step], past)
            past = (K_stored, K_stored)  # reuse K as V for simplicity

        # After 20 steps: stored = [sink0, sink1, recent_16, recent_17, recent_18, recent_19]
        for w_idx in range(W):
            global_step = 20 - W + w_idx   # 16, 17, 18, 19
            expected_val = float(global_step)
            stored_val = K_stored[0, 0, S + w_idx, 0].item()
            assert abs(stored_val - expected_val) < 1e-5, \
                f"Window slot {w_idx}: expected value {expected_val}, got {stored_val}"

    def test_no_sink_naive_sliding_window(self):
        """With num_sink_tokens=0, only the last W tokens are kept — naive sliding window."""
        W, S = 5, 0
        sizes, policy = self._run_policy(n_steps=20, window_size=W, num_sink_tokens=S)
        for i, sz in enumerate(sizes):
            expected = min(i + 1, W)
            assert sz == expected, \
                f"Step {i}: naive window expected T_kept={expected}, got {sz}"

    def test_mask_always_all_true(self):
        """Eviction removes rows, so the mask over kept rows is always all-True."""
        from app.cache_policies.sliding_window import SlidingWindowPolicy
        policy = SlidingWindowPolicy(window_size=6, num_sink_tokens=2)
        B, H, d_head = 1, 4, 16
        past = None
        for step in range(20):
            k = torch.randn(B, H, 1, d_head)
            K_stored, V_stored, mask = policy.update(step, 0, k, k, past)
            past = (K_stored, V_stored)
            assert mask.all(), \
                f"Step {step}: mask has False entries — sliding_window should remove rows, not mask them"

    def test_reset_clears_store(self):
        from app.cache_policies.sliding_window import SlidingWindowPolicy
        policy = SlidingWindowPolicy(window_size=8, num_sink_tokens=2)
        B, H, d_head = 1, 4, 16
        k = torch.randn(B, H, 1, d_head)
        for step in range(5):
            K_s, V_s, _ = policy.update(step, 0, k, k, None if step == 0 else (K_s, V_s))
        assert policy.memory_tokens_used() == 5
        policy.reset()
        assert policy.memory_tokens_used() == 0, "reset() did not clear the stored cache"


# ===========================================================================
# 4. /simulate endpoint — full integration tests
# ===========================================================================

class TestSimulateEndpoint:

    @pytest.fixture(scope="class")
    @classmethod
    def client(cls):
        from fastapi.testclient import TestClient
        from app.main import app
        return TestClient(app)

    # --- Structural response validation helper ---
    def _assert_well_formed(self, data: dict, policy: str) -> None:
        """Assert the /simulate JSON response has all required fields."""
        assert "episode" in data, "Response missing 'episode' key"
        assert "simulation" in data, "Response missing 'simulation' key"

        ep = data["episode"]
        sim = data["simulation"]

        # Episode fields
        for field in ("text", "token_ids", "fact_positions",
                      "question_start", "answer"):
            assert field in ep, f"episode missing '{field}'"
        assert isinstance(ep["token_ids"], list)
        assert len(ep["token_ids"]) > 0

        # Simulation fields
        for field in ("policy", "policy_params", "steps",
                      "final_answer", "ground_truth", "correct", "policy_info"):
            assert field in sim, f"simulation missing '{field}'"

        assert sim["policy"] == policy
        assert isinstance(sim["correct"], bool)
        assert isinstance(sim["steps"], list)
        assert len(sim["steps"]) == len(ep["token_ids"]), (
            f"steps count ({len(sim['steps'])}) must equal "
            f"token_ids count ({len(ep['token_ids'])})"
        )

        # Step fields
        for i, step in enumerate(sim["steps"]):
            for sf in ("step", "token_id", "token_char",
                       "visible_token_indices", "cache_size_tokens",
                       "cache_size_bytes"):
                assert sf in step, f"Step {i} missing '{sf}'"
            assert step["step"] == i
            assert isinstance(step["visible_token_indices"], list)
            assert step["cache_size_tokens"] == len(step["visible_token_indices"])

    def test_full_cache_returns_200(self, client):
        resp = client.post("/simulate", json={
            "policy": "full_cache",
            "n_facts": 2, "seq_len": 80, "question_target": 0, "seed": 7,
        })
        assert resp.status_code == 200, f"Got {resp.status_code}: {resp.text}"

    def test_full_cache_response_well_formed(self, client):
        resp = client.post("/simulate", json={
            "policy": "full_cache",
            "n_facts": 2, "seq_len": 80, "question_target": 0, "seed": 7,
        })
        self._assert_well_formed(resp.json(), "full_cache")

    def test_full_cache_visible_indices_monotonically_grow(self, client):
        """Under full_cache, visible_token_indices at step i must be [0, 1, ..., i]."""
        resp = client.post("/simulate", json={
            "policy": "full_cache",
            "n_facts": 1, "seq_len": 50, "question_target": 0, "seed": 3,
        })
        steps = resp.json()["simulation"]["steps"]
        for i, step in enumerate(steps):
            expected = list(range(i + 1))
            assert step["visible_token_indices"] == expected, (
                f"Step {i}: expected visible indices {expected}, "
                f"got {step['visible_token_indices']}"
            )

    def test_full_cache_memory_grows_linearly(self, client):
        """Each step adds exactly 1 token — cache_size_tokens must equal step+1."""
        resp = client.post("/simulate", json={
            "policy": "full_cache",
            "n_facts": 1, "seq_len": 50, "question_target": 0, "seed": 3,
        })
        steps = resp.json()["simulation"]["steps"]
        for i, step in enumerate(steps):
            assert step["cache_size_tokens"] == i + 1, \
                f"Step {i}: expected cache_size_tokens={i+1}, got {step['cache_size_tokens']}"

    def test_sliding_window_returns_200(self, client):
        resp = client.post("/simulate", json={
            "policy": "sliding_window",
            "window_size": 16, "num_sink_tokens": 2,
            "n_facts": 2, "seq_len": 80, "question_target": 0, "seed": 7,
        })
        assert resp.status_code == 200, f"Got {resp.status_code}: {resp.text}"

    def test_sliding_window_response_well_formed(self, client):
        resp = client.post("/simulate", json={
            "policy": "sliding_window",
            "window_size": 16, "num_sink_tokens": 2,
            "n_facts": 2, "seq_len": 80, "question_target": 0, "seed": 7,
        })
        self._assert_well_formed(resp.json(), "sliding_window")

    def test_sliding_window_cache_bounded(self, client):
        """After filling up, cache_size_tokens must never exceed window+sinks."""
        W, S = 12, 3
        resp = client.post("/simulate", json={
            "policy": "sliding_window",
            "window_size": W, "num_sink_tokens": S,
            "n_facts": 2, "seq_len": 100, "question_target": 0, "seed": 5,
        })
        budget = W + S
        steps = resp.json()["simulation"]["steps"]
        for step in steps:
            assert step["cache_size_tokens"] <= budget, (
                f"Step {step['step']}: cache_size_tokens={step['cache_size_tokens']} "
                f"exceeds budget={budget}"
            )

    def test_sliding_window_sink_indices_always_present(self, client):
        """Global token indices 0..num_sink_tokens-1 must appear in every step's
        visible_token_indices once the sink budget is filled."""
        S = 3
        resp = client.post("/simulate", json={
            "policy": "sliding_window",
            "window_size": 10, "num_sink_tokens": S,
            "n_facts": 2, "seq_len": 80, "question_target": 0, "seed": 9,
        })
        steps = resp.json()["simulation"]["steps"]
        # Only check steps after sinks have been filled (step >= S)
        for step in steps[S:]:
            vis = step["visible_token_indices"]
            for sink_idx in range(S):
                assert sink_idx in vis, (
                    f"Step {step['step']}: sink token {sink_idx} not in "
                    f"visible_token_indices {vis}"
                )

    def test_unknown_policy_returns_400(self, client):
        resp = client.post("/simulate", json={
            "policy": "time_travel_cache",
            "n_facts": 1, "seq_len": 50, "question_target": 0, "seed": 1,
        })
        assert resp.status_code == 400

    def test_bad_question_target_returns_400(self, client):
        resp = client.post("/simulate", json={
            "policy": "full_cache",
            "n_facts": 2, "seq_len": 80, "question_target": 5, "seed": 1,
        })
        assert resp.status_code == 400

    def test_step_still_501(self, client):
        resp = client.post("/step")
        assert resp.status_code == 501

    def test_cache_size_bytes_formula(self, client):
        """cache_size_bytes must equal cache_size_tokens * 2048."""
        resp = client.post("/simulate", json={
            "policy": "full_cache",
            "n_facts": 1, "seq_len": 40, "question_target": 0, "seed": 2,
        })
        BYTES_PER_TOKEN = 2048   # 4 layers × 2 (K+V) × 4 heads × 16 d_head × 4 bytes
        for step in resp.json()["simulation"]["steps"]:
            expected = step["cache_size_tokens"] * BYTES_PER_TOKEN
            assert step["cache_size_bytes"] == expected, \
                f"Step {step['step']}: bytes={step['cache_size_bytes']} != {expected}"
