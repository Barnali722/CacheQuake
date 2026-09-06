# backend/tests/test_smoke.py
"""
Day 1 smoke tests — verify the skeleton actually runs.

These tests do NOT require a trained model.  They check:
    1. Vocab encodes/decodes correctly.
    2. The toy Transformer forward pass runs and returns the right shapes.
    3. The needle-in-haystack generator produces valid episodes.
    4. The full-cache policy round-trips correctly.
    5. The FastAPI /health endpoint returns 200.

Run from the backend/ directory:
    pytest tests/test_smoke.py -v
"""

import sys, os
# Make sure the backend/ directory is on the path so imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
import torch


# ---------------------------------------------------------------------------
# 1. Vocabulary
# ---------------------------------------------------------------------------

class TestVocab:
    def test_vocab_size(self):
        from app.model.vocab import VOCAB_SIZE
        # 26 letters + 10 digits + 1 space + 5 punct = 42 printable + PAD + UNK = 44
        assert VOCAB_SIZE == 44, f"Expected 44, got {VOCAB_SIZE}"

    def test_encode_decode_roundtrip(self):
        from app.model.vocab import encode, decode
        text = "hello world 123"
        assert decode(encode(text)) == text

    def test_unknown_char_maps_to_unk(self):
        from app.model.vocab import encode, UNK_ID
        ids = encode("@#$")  # none of these are in the vocab
        assert all(i == UNK_ID for i in ids)

    def test_encode_returns_list_of_ints(self):
        from app.model.vocab import encode
        ids = encode("abc")
        assert isinstance(ids, list)
        assert all(isinstance(i, int) for i in ids)


# ---------------------------------------------------------------------------
# 2. Toy Transformer shapes
# ---------------------------------------------------------------------------

class TestToyTransformer:
    @pytest.fixture(scope="class")
    @classmethod
    def model(cls):
        from app.model.toy_transformer import ToyTransformer
        m = ToyTransformer(vocab_size=44, d_model=64, n_heads=4,
                           n_layers=4, max_seq_len=512)
        m.eval()
        return m

    def test_forward_shape_no_cache(self, model):
        """Basic forward pass without any cache."""
        B, T = 2, 16
        ids = torch.randint(0, 44, (B, T))
        with torch.no_grad():
            logits, present_caches = model(ids)

        assert logits.shape == (B, T, 44), \
            f"logits shape mismatch: {logits.shape}"
        assert len(present_caches) == 4, \
            f"expected 4 present_caches, got {len(present_caches)}"

    def test_present_cache_shapes(self, model):
        """K and V tensors must have correct head-split shapes."""
        B, T = 1, 8
        ids = torch.randint(0, 40, (B, T))
        H, d_head = 4, 16  # d_model=64, n_heads=4 → d_head=16
        with torch.no_grad():
            _, present_caches = model(ids)

        for layer_idx, (k, v) in enumerate(present_caches):
            assert k.shape == (B, H, T, d_head), \
                f"Layer {layer_idx} K shape: {k.shape}"
            assert v.shape == (B, H, T, d_head), \
                f"Layer {layer_idx} V shape: {v.shape}"

    def test_forward_with_cache(self, model):
        """Two-step forward: prefill then single next-token step."""
        B, T_prefill, T_step = 1, 10, 1
        H, d_head = 4, 16

        # Prefill
        prefill_ids = torch.randint(0, 44, (B, T_prefill))
        with torch.no_grad():
            _, present_caches = model(prefill_ids)

        # Simulate full-cache: just use the returned K/V directly
        # (no policy applied here — just checking shapes)
        past_caches = [(k, v) for k, v in present_caches]

        # Next step
        step_ids = torch.randint(0, 40, (B, T_step))
        with torch.no_grad():
            logits, step_caches = model(step_ids, past_caches=past_caches)

        # Logits should be for the single new token
        assert logits.shape == (B, T_step, 44)
        # New K/V should cover only the new token
        k_new, v_new = step_caches[0]
        assert k_new.shape == (B, H, T_step, d_head)

    def test_parameter_count_reasonable(self, model):
        """Model should be tiny — sanity-check the param count."""
        n_params = model.count_parameters()
        # With d_model=64, 4 layers, vocab=40: expect roughly 100k–500k params
        assert 50_000 < n_params < 1_000_000, \
            f"Unexpected param count: {n_params}"


# ---------------------------------------------------------------------------
# 3. Needle-in-haystack generator
# ---------------------------------------------------------------------------

class TestNeedleHaystack:
    @pytest.fixture(scope="class")
    @classmethod
    def task(cls):
        from app.tasks.needle_haystack import NeedleHaystackTask
        return NeedleHaystackTask(seed=99)

    def test_generate_returns_episode(self, task):
        from app.tasks.needle_haystack import NeedleHaystackEpisode
        ep = task.generate(n_facts=3, seq_len=200, question_target=1)
        assert isinstance(ep, NeedleHaystackEpisode)

    def test_token_ids_are_valid(self, task):
        from app.model.vocab import VOCAB_SIZE
        ep = task.generate(n_facts=2, seq_len=128, question_target=0)
        assert all(0 <= t < VOCAB_SIZE for t in ep.token_ids), \
            "Some token ids are outside the vocabulary range"

    def test_fact_positions_in_range(self, task):
        ep = task.generate(n_facts=3, seq_len=256, question_target=0)
        n = len(ep.token_ids)
        for name, pos in ep.fact_positions.items():
            assert 0 <= pos < n, \
                f"Fact '{name}' position {pos} out of range [0, {n})"

    def test_question_start_after_facts(self, task):
        ep = task.generate(n_facts=2, seq_len=200, question_target=0)
        for name, pos in ep.fact_positions.items():
            assert ep.question_start > pos, \
                f"question_start ({ep.question_start}) not after fact '{name}' ({pos})"

    def test_answer_in_vault_codes(self, task):
        ep = task.generate(n_facts=4, seq_len=300, question_target=2)
        assert ep.answer in ep.vault_codes.values()

    def test_too_many_facts_raises(self, task):
        with pytest.raises(ValueError):
            task.generate(n_facts=9, seq_len=256, question_target=0)

    def test_bad_question_target_raises(self, task):
        with pytest.raises(ValueError):
            task.generate(n_facts=2, seq_len=128, question_target=5)


# ---------------------------------------------------------------------------
# 4. Full-cache policy
# ---------------------------------------------------------------------------

class TestFullCachePolicy:
    def _make_kv(self, B, H, T, d_head):
        """Helper to create random K/V tensors."""
        k = torch.randn(B, H, T, d_head)
        v = torch.randn(B, H, T, d_head)
        return k, v

    def test_first_call_no_past(self):
        from app.cache_policies.full_cache import FullCachePolicy
        policy = FullCachePolicy()
        k, v = self._make_kv(B=1, H=4, T=5, d_head=16)
        K_stored, V_stored, mask = policy.update(step=0, layer_idx=0,
                                                  k=k, v=v, past_cache=None)
        assert K_stored.shape == (1, 4, 5, 16)
        assert V_stored.shape == (1, 4, 5, 16)
        assert mask.shape == (1, 5)
        assert mask.all(), "Full-cache mask should be all-True"

    def test_accumulates_tokens(self):
        from app.cache_policies.full_cache import FullCachePolicy
        policy = FullCachePolicy()
        B, H, d_head = 1, 4, 16

        K_stored, V_stored, mask = policy.update(
            step=0, layer_idx=0,
            k=torch.randn(B, H, 3, d_head),
            v=torch.randn(B, H, 3, d_head),
            past_cache=None,
        )
        K_stored, V_stored, mask = policy.update(
            step=1, layer_idx=0,
            k=torch.randn(B, H, 1, d_head),
            v=torch.randn(B, H, 1, d_head),
            past_cache=(K_stored, V_stored),
        )
        assert K_stored.shape[2] == 4, \
            f"Expected 4 accumulated tokens, got {K_stored.shape[2]}"
        assert policy.memory_tokens_used() == 4

    def test_reset_clears_counter(self):
        from app.cache_policies.full_cache import FullCachePolicy
        policy = FullCachePolicy()
        k, v = self._make_kv(B=1, H=4, T=5, d_head=16)
        policy.update(0, 0, k, v, None)
        assert policy.memory_tokens_used() == 5
        policy.reset()
        assert policy.memory_tokens_used() == 0


# ---------------------------------------------------------------------------
# 5. FastAPI /health endpoint
# ---------------------------------------------------------------------------

class TestHealthEndpoint:
    def test_health_returns_200(self):
        from fastapi.testclient import TestClient
        from app.main import app
        client = TestClient(app)
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_health_contains_expected_keys(self):
        from fastapi.testclient import TestClient
        from app.main import app
        client = TestClient(app)
        data = client.get("/health").json()
        assert data["status"] == "ok"
        assert data["vocab"]["vocab_size"] == 44
        assert data["model"]["d_model"] == 64
        assert "cache_policies" in data
        assert len(data["cache_policies"]) == 4

    def test_simulate_returns_200_or_501(self):
        """Smoke-check /simulate is reachable — full contract tested in test_day2.py."""
        from fastapi.testclient import TestClient
        from app.main import app
        client = TestClient(app)
        resp = client.post("/simulate",
                           json={"policy": "full_cache", "n_facts": 1,
                                 "seq_len": 64, "question_target": 0, "seed": 1})
        # Accept 200 (implemented) or 501 (still stub) — both are valid here.
        assert resp.status_code in (200, 501)

    def test_step_returns_501(self):
        from fastapi.testclient import TestClient
        from app.main import app
        client = TestClient(app)
        resp = client.post("/step")
        assert resp.status_code == 501
