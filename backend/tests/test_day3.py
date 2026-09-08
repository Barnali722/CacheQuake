# backend/tests/test_day3.py
"""
Day 3 regression tests for CacheQuake.

What these tests verify:
    1. HeavyHitterPolicy retains the highest-scoring tokens and evicts the rest.
    2. HeavyHitterPolicy always keeps the most recently added token.
    3. HeavyHitterPolicy stays within the budget at all times.
    4. HeavyHitterPolicy.reset() clears all state cleanly.
    5. HeavyHitterPolicy._global_indices tracks exactly which global positions survive.
    6. BDHInspiredState.M stays exactly [n_heads, state_size, d_head] for any T.
    7. BDHInspiredState.memory_tokens_used() == state_size always (constant).
    8. BDHInspiredState.reset() re-zeros M.
    9. BDHInspiredState docstring label check — required phrase appears in source.
   10. /simulate with "heavy_hitter"      returns 200 + well-formed JSON.
   11. /simulate with "bdh_inspired_state" returns 200 + well-formed JSON.
   12. /simulate heavy_hitter  cache_size_tokens <= budget at every step.
   13. /simulate bdh_inspired_state cache_size_tokens == state_size at every step.
   14. /simulate with new budget/state_size/decay params does not break old fields.

Run from backend/:
    pytest tests/test_day3.py -v
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import inspect
import pytest
import torch


# ---------------------------------------------------------------------------
# 1–5. HeavyHitterPolicy unit tests
# ---------------------------------------------------------------------------

class TestHeavyHitterPolicy:
    """Unit tests for HeavyHitterPolicy (token-level, no model involved)."""

    B, H, d_head = 1, 4, 16

    def _make_k_v(self, value: float) -> tuple[torch.Tensor, torch.Tensor]:
        """Make a [B, H, 1, d_head] tensor filled with `value`."""
        k = torch.full((self.B, self.H, 1, self.d_head), value)
        v = torch.full((self.B, self.H, 1, self.d_head), value)
        return k, v

    def test_budget_never_exceeded(self):
        """T_kept must not exceed budget at any point."""
        from app.cache_policies.heavy_hitter import HeavyHitterPolicy
        policy = HeavyHitterPolicy(budget=4)
        policy.reset()

        for step in range(20):
            k, v = self._make_k_v(float(step))
            K_out, V_out, mask = policy.update(step, layer_idx=0, k=k, v=v,
                                               past_cache=None)
            assert K_out.shape[2] <= 4, (
                f"Step {step}: stored {K_out.shape[2]} rows, budget is 4"
            )

    def test_most_recent_token_always_kept(self):
        """The token added at the current step must always be in K_stored."""
        from app.cache_policies.heavy_hitter import HeavyHitterPolicy
        budget = 3
        policy = HeavyHitterPolicy(budget=budget)
        policy.reset()

        for step in range(15):
            # Give a recognisable value for each step
            k = torch.full((self.B, self.H, 1, self.d_head), float(step + 1) * 10.0)
            v = torch.full((self.B, self.H, 1, self.d_head), float(step + 1) * 10.0)
            K_out, V_out, mask = policy.update(step, layer_idx=0, k=k, v=v,
                                               past_cache=None)
            # The last row of K_out must be the current token
            last_row_val = K_out[0, 0, -1, 0].item()
            expected_val = float(step + 1) * 10.0
            assert abs(last_row_val - expected_val) < 1e-3, (
                f"Step {step}: expected last-row val {expected_val}, got {last_row_val}"
            )

    def test_mask_is_always_all_true(self):
        """cache_mask must be all-True over whatever rows are kept."""
        from app.cache_policies.heavy_hitter import HeavyHitterPolicy
        policy = HeavyHitterPolicy(budget=5)
        policy.reset()

        for step in range(12):
            k, v = self._make_k_v(1.0)
            _, _, mask = policy.update(step, layer_idx=0, k=k, v=v, past_cache=None)
            assert mask.all(), f"Step {step}: mask has False entries"

    def test_reset_clears_state(self):
        """reset() must zero out everything so the next episode starts fresh."""
        from app.cache_policies.heavy_hitter import HeavyHitterPolicy
        policy = HeavyHitterPolicy(budget=4)
        policy.reset()

        for step in range(10):
            k, v = self._make_k_v(1.0)
            policy.update(step, layer_idx=0, k=k, v=v, past_cache=None)

        policy.reset()
        assert len(policy._store) == 0,          "store not cleared after reset"
        assert len(policy._global_indices) == 0, "_global_indices not cleared"
        assert policy._tokens_seen == 0,          "_tokens_seen not reset"
        assert policy._total_evictions == 0,      "_total_evictions not reset"
        assert policy.memory_tokens_used() == 0, "memory_tokens_used not 0 after reset"

    def test_global_indices_matches_kept_rows(self):
        """_global_indices must have the same length as K_stored at all times."""
        from app.cache_policies.heavy_hitter import HeavyHitterPolicy
        policy = HeavyHitterPolicy(budget=5)
        policy.reset()

        for step in range(20):
            k, v = self._make_k_v(float(step))
            K_out, _, _ = policy.update(step, layer_idx=0, k=k, v=v, past_cache=None)
            T_kept = K_out.shape[2]
            assert len(policy._global_indices) == T_kept, (
                f"Step {step}: _global_indices len {len(policy._global_indices)} "
                f"!= T_kept {T_kept}"
            )

    def test_high_score_token_survives_eviction(self):
        """A token with high dot-product similarity to all future queries should
        survive eviction when there are other low-similarity tokens."""
        from app.cache_policies.heavy_hitter import HeavyHitterPolicy

        budget = 3
        policy = HeavyHitterPolicy(budget=budget)
        policy.reset()

        # Step 0: inject a "needle" token with a very distinctive key vector
        #         (large values → high dot products with all future queries)
        d = self.d_head
        needle_k = torch.ones(self.B, self.H, 1, d) * 100.0
        needle_v = torch.ones(self.B, self.H, 1, d)
        policy.update(0, layer_idx=0, k=needle_k, v=needle_v, past_cache=None)

        # Steps 1–5: inject filler tokens with near-zero key vectors
        for step in range(1, 6):
            filler_k = torch.zeros(self.B, self.H, 1, d)
            filler_v = torch.zeros(self.B, self.H, 1, d)
            policy.update(step, layer_idx=0, k=filler_k, v=filler_v, past_cache=None)

        # Step 5 forces evictions (6 tokens > budget=3).
        # The needle (step 0) should have accumulated the highest score
        # because every subsequent query's key dot-products with it are large.
        # Check: global position 0 is still in _global_indices.
        assert 0 in policy._global_indices, (
            f"Needle (global pos 0) was evicted; surviving: {policy._global_indices}"
        )

    def test_policy_info_keys(self):
        from app.cache_policies.heavy_hitter import HeavyHitterPolicy
        policy = HeavyHitterPolicy(budget=8)
        policy.reset()
        info = policy.policy_info()
        for key in ("policy", "budget", "tokens_cached", "tokens_seen", "evictions"):
            assert key in info, f"policy_info missing key '{key}'"
        assert info["policy"] == "heavy_hitter"


# ---------------------------------------------------------------------------
# 6–9. BDHInspiredState unit tests
# ---------------------------------------------------------------------------

class TestBDHInspiredState:
    """Unit tests for BDHInspiredState.

    Toy layer inspired by BDH, not BDH itself.
    """

    B, H, state_size, d_head = 1, 4, 8, 16

    def _make_k_v(self) -> tuple[torch.Tensor, torch.Tensor]:
        k = torch.randn(self.B, self.H, 1, self.d_head)
        v = torch.randn(self.B, self.H, 1, self.d_head)
        return k, v

    def test_M_shape_stays_constant(self):
        """M must remain [n_heads, state_size, d_head] after any number of writes."""
        from app.cache_policies.bdh_inspired_state import BDHInspiredState
        policy = BDHInspiredState(state_size=self.state_size, d_head=self.d_head,
                                  n_heads=self.H)
        policy.reset()
        expected_shape = (self.H, self.state_size, self.d_head)

        for step in range(50):  # far more steps than state_size
            k, v = self._make_k_v()
            K_out, V_out, mask = policy.update(step, layer_idx=0, k=k, v=v,
                                               past_cache=None)
            assert policy.M.shape == expected_shape, (
                f"Step {step}: M.shape {policy.M.shape} != {expected_shape}"
            )

    def test_K_stored_shape_is_state_size(self):
        """K_stored and V_stored must have T_kept == state_size at every step."""
        from app.cache_policies.bdh_inspired_state import BDHInspiredState
        policy = BDHInspiredState(state_size=self.state_size, d_head=self.d_head,
                                  n_heads=self.H)
        policy.reset()

        for step in range(20):
            k, v = self._make_k_v()
            K_out, V_out, mask = policy.update(step, layer_idx=0, k=k, v=v,
                                               past_cache=None)
            assert K_out.shape[2] == self.state_size, (
                f"Step {step}: K_out.shape[2] = {K_out.shape[2]}, "
                f"expected {self.state_size}"
            )
            assert V_out.shape[2] == self.state_size

    def test_memory_tokens_used_is_constant(self):
        """memory_tokens_used() must always return state_size."""
        from app.cache_policies.bdh_inspired_state import BDHInspiredState
        policy = BDHInspiredState(state_size=self.state_size, d_head=self.d_head,
                                  n_heads=self.H)
        policy.reset()

        for step in range(30):
            k, v = self._make_k_v()
            policy.update(step, layer_idx=0, k=k, v=v, past_cache=None)
            assert policy.memory_tokens_used() == self.state_size, (
                f"Step {step}: memory_tokens_used() = {policy.memory_tokens_used()}, "
                f"expected {self.state_size}"
            )

    def test_reset_zeros_M(self):
        """reset() must zero-out M so each episode starts fresh."""
        from app.cache_policies.bdh_inspired_state import BDHInspiredState
        policy = BDHInspiredState(state_size=self.state_size, d_head=self.d_head,
                                  n_heads=self.H)
        policy.reset()

        # Write some data
        for step in range(5):
            k, v = self._make_k_v()
            policy.update(step, layer_idx=0, k=k, v=v, past_cache=None)

        assert policy.M is not None
        assert policy.M.abs().sum().item() > 0, "M should be non-zero after writes"

        policy.reset()
        assert policy.M.abs().sum().item() == 0.0, "M should be all-zero after reset"

    def test_mask_always_all_true(self):
        """cache_mask must be all-True (state_size entries) at every step."""
        from app.cache_policies.bdh_inspired_state import BDHInspiredState
        policy = BDHInspiredState(state_size=self.state_size, d_head=self.d_head,
                                  n_heads=self.H)
        policy.reset()

        for step in range(10):
            k, v = self._make_k_v()
            _, _, mask = policy.update(step, layer_idx=0, k=k, v=v, past_cache=None)
            assert mask.shape == (self.B, self.state_size), \
                f"mask shape {mask.shape} != (B={self.B}, state_size={self.state_size})"
            assert mask.all(), f"Step {step}: mask has False entries"

    def test_M_changes_after_write(self):
        """M must change when a non-zero (k, v) is written."""
        from app.cache_policies.bdh_inspired_state import BDHInspiredState
        policy = BDHInspiredState(state_size=self.state_size, d_head=self.d_head,
                                  n_heads=self.H, decay=0.9)
        policy.reset()

        M_before = policy.M.clone()
        k, v = self._make_k_v()
        policy.update(0, layer_idx=0, k=k, v=v, past_cache=None)
        M_after = policy.M

        assert not torch.allclose(M_before, M_after), (
            "M did not change after a non-zero (k,v) write"
        )

    def test_docstring_label_present(self):
        """The required disclaimer phrase must appear in bdh_inspired_state.py.

        This is a contract requirement, not just a style preference.  The
        phrase 'toy layer inspired by BDH, not BDH itself' must appear at
        least once in the module source to make the constraint machine-checkable.
        """
        import app.cache_policies.bdh_inspired_state as bdh_module
        source = inspect.getsource(bdh_module)
        required_phrase = "toy layer inspired by BDH, not BDH itself"
        assert required_phrase in source, (
            f"Required phrase '{required_phrase}' not found in bdh_inspired_state.py. "
            "This label is a project constraint — see README."
        )

    def test_policy_info_keys(self):
        from app.cache_policies.bdh_inspired_state import BDHInspiredState
        policy = BDHInspiredState(state_size=self.state_size, d_head=self.d_head,
                                  n_heads=self.H)
        policy.reset()
        info = policy.policy_info()
        for key in ("policy", "state_size", "decay", "tokens_seen", "note"):
            assert key in info, f"policy_info missing key '{key}'"
        assert info["policy"] == "bdh_inspired_state"
        # The "note" must reinforce the disclaimer
        assert "toy layer" in info["note"]


# ---------------------------------------------------------------------------
# 10–14. /simulate endpoint integration tests (both new policies)
# ---------------------------------------------------------------------------

class TestSimulateNewPolicies:
    """Integration tests for /simulate with heavy_hitter and bdh_inspired_state."""

    @pytest.fixture(scope="class")
    @classmethod
    def client(cls):
        from fastapi.testclient import TestClient
        from app.main import app
        return TestClient(app)

    # ---- heavy_hitter ----

    def test_heavy_hitter_returns_200(self, client):
        resp = client.post("/simulate", json={
            "policy": "heavy_hitter",
            "budget": 16,
            "n_facts": 2,
            "seq_len": 60,
            "question_target": 0,
            "seed": 7,
        })
        assert resp.status_code == 200, resp.text

    def test_heavy_hitter_response_well_formed(self, client):
        resp = client.post("/simulate", json={
            "policy": "heavy_hitter",
            "budget": 16,
            "n_facts": 2,
            "seq_len": 60,
            "question_target": 0,
            "seed": 7,
        })
        data = resp.json()
        # Top-level keys
        assert "episode"    in data
        assert "simulation" in data
        sim = data["simulation"]
        # Simulation keys
        for key in ("policy", "policy_params", "steps", "final_answer",
                    "ground_truth", "correct", "policy_info"):
            assert key in sim, f"simulation missing key '{key}'"
        assert sim["policy"] == "heavy_hitter"
        # Steps structure
        assert len(sim["steps"]) > 0
        step0 = sim["steps"][0]
        for key in ("step", "token_id", "token_char",
                    "visible_token_indices", "cache_size_tokens", "cache_size_bytes"):
            assert key in step0, f"step missing key '{key}'"

    def test_heavy_hitter_cache_bounded(self, client):
        """cache_size_tokens must never exceed budget."""
        budget = 12
        resp = client.post("/simulate", json={
            "policy": "heavy_hitter",
            "budget": budget,
            "n_facts": 2,
            "seq_len": 60,
            "question_target": 0,
            "seed": 7,
        })
        data = resp.json()
        for step in data["simulation"]["steps"]:
            assert step["cache_size_tokens"] <= budget, (
                f"Step {step['step']}: cache_size_tokens {step['cache_size_tokens']} "
                f"> budget {budget}"
            )

    def test_heavy_hitter_policy_info(self, client):
        """policy_info should contain budget, tokens_cached, evictions."""
        resp = client.post("/simulate", json={
            "policy": "heavy_hitter",
            "budget": 12,
            "n_facts": 2,
            "seq_len": 60,
            "question_target": 0,
            "seed": 7,
        })
        info = resp.json()["simulation"]["policy_info"]
        assert info["budget"] == 12
        assert "evictions" in info
        assert "tokens_cached" in info

    # ---- bdh_inspired_state ----

    def test_bdh_returns_200(self, client):
        resp = client.post("/simulate", json={
            "policy":     "bdh_inspired_state",
            "state_size": 16,
            "decay":      0.9,
            "n_facts":    2,
            "seq_len":    60,
            "question_target": 0,
            "seed":       7,
        })
        assert resp.status_code == 200, resp.text

    def test_bdh_response_well_formed(self, client):
        resp = client.post("/simulate", json={
            "policy":     "bdh_inspired_state",
            "state_size": 16,
            "decay":      0.9,
            "n_facts":    2,
            "seq_len":    60,
            "question_target": 0,
            "seed":       7,
        })
        data = resp.json()
        assert "episode"    in data
        assert "simulation" in data
        sim = data["simulation"]
        assert sim["policy"] == "bdh_inspired_state"
        assert len(sim["steps"]) > 0

    def test_bdh_cache_size_constant(self, client):
        """cache_size_tokens must equal state_size at every step (constant memory)."""
        state_size = 16
        resp = client.post("/simulate", json={
            "policy":     "bdh_inspired_state",
            "state_size": state_size,
            "decay":      0.9,
            "n_facts":    2,
            "seq_len":    60,
            "question_target": 0,
            "seed":       7,
        })
        data = resp.json()
        for step in data["simulation"]["steps"]:
            assert step["cache_size_tokens"] == state_size, (
                f"Step {step['step']}: cache_size_tokens {step['cache_size_tokens']} "
                f"!= state_size {state_size}"
            )

    def test_bdh_policy_info(self, client):
        """policy_info must contain state_size, decay, and the note label."""
        resp = client.post("/simulate", json={
            "policy":     "bdh_inspired_state",
            "state_size": 16,
            "decay":      0.85,
            "n_facts":    2,
            "seq_len":    60,
            "question_target": 0,
            "seed":       7,
        })
        info = resp.json()["simulation"]["policy_info"]
        assert info["state_size"] == 16
        assert abs(info["decay"] - 0.85) < 1e-6
        assert "note" in info
        assert "toy layer" in info["note"]

    def test_new_params_do_not_break_schema(self, client):
        """Sending budget/state_size/decay with full_cache must still return 200."""
        resp = client.post("/simulate", json={
            "policy":     "full_cache",
            "budget":     32,       # ignored for full_cache
            "state_size": 16,       # ignored for full_cache
            "decay":      0.9,      # ignored for full_cache
            "n_facts":    2,
            "seq_len":    50,
            "question_target": 0,
            "seed":       1,
        })
        assert resp.status_code == 200, (
            f"full_cache rejected extra params: {resp.text}"
        )

    def test_invalid_decay_rejected(self, client):
        """decay >= 1.0 must be rejected with 422."""
        resp = client.post("/simulate", json={
            "policy":     "bdh_inspired_state",
            "state_size": 16,
            "decay":      1.0,   # invalid: must be < 1.0
            "n_facts":    2,
            "seq_len":    50,
            "question_target": 0,
        })
        assert resp.status_code == 422, (
            f"Expected 422 for decay=1.0, got {resp.status_code}"
        )
