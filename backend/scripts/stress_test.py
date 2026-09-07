"""
Stress test script for /simulate endpoint.
Tests concurrent requests, edge cases, and error handling.
"""
import sys
import time
import json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_edge_cases():
    """Test edge cases and error handling."""
    print("\n" + "=" * 70)
    print("EDGE CASE TESTS")
    print("=" * 70)
    
    # Test 1: budget = 0 (should fail gracefully or work with minimal cache)
    print("\n[Test 1] budget=0")
    try:
        resp = client.post("/simulate", json={
            "policy": "heavy_hitter",
            "seq_len": 32,
            "n_facts": 4,
            "question_target": 2,
            "seed": 42,
            "budget": 0
        })
        if resp.status_code == 200:
            print(f"  ✓ Status 200 - Accepted budget=0")
            result = resp.json()
            sim = result.get('simulation', {})
            print(f"    Steps: {len(sim.get('steps', []))}, Answer: {sim.get('final_answer', 'N/A')}")
        elif 400 <= resp.status_code < 500:
            print(f"  ✓ Status {resp.status_code} - Rejected with message: {resp.json().get('detail', 'N/A')[:60]}")
        else:
            print(f"  ✗ Unexpected status {resp.status_code}")
    except Exception as e:
        print(f"  ✗ Exception: {type(e).__name__}: {str(e)[:60]}")
    
    # Test 2: budget = 1 (minimal cache)
    print("\n[Test 2] budget=1")
    try:
        resp = client.post("/simulate", json={
            "policy": "sliding_window",
            "seq_len": 32,
            "n_facts": 4,
            "question_target": 2,
            "seed": 42,
            "window_size": 1,
            "num_sink_tokens": 0
        })
        if resp.status_code == 200:
            print(f"  ✓ Status 200 - Works with budget=1")
            result = resp.json()
            sim = result.get('simulation', {})
            print(f"    Max cache size: {max(s['cache_size_tokens'] for s in sim.get('steps', []))}")
        else:
            print(f"  ✓ Status {resp.status_code} - Rejected: {resp.json().get('detail', 'N/A')[:60]}")
    except Exception as e:
        print(f"  ✗ Exception: {type(e).__name__}: {str(e)[:60]}")
    
    # Test 3: Very long sequence (max frontend might allow)
    print("\n[Test 3] seq_len=256 (long sequence)")
    try:
        start = time.perf_counter()
        resp = client.post("/simulate", json={
            "policy": "sliding_window",
            "seq_len": 256,
            "n_facts": 8,
            "question_target": 4,
            "seed": 42,
            "window_size": 64,
            "num_sink_tokens": 4
        })
        elapsed_ms = (time.perf_counter() - start) * 1000
        if resp.status_code == 200:
            print(f"  ✓ Status 200 - Completed in {elapsed_ms:.1f} ms")
            result = resp.json()
            sim = result.get('simulation', {})
            print(f"    Steps: {len(sim.get('steps', []))}")
        else:
            print(f"  ✗ Status {resp.status_code}: {resp.json().get('detail', 'N/A')[:60]}")
    except Exception as e:
        print(f"  ✗ Exception: {type(e).__name__}: {str(e)[:60]}")
    
    # Test 4: Invalid policy name
    print("\n[Test 4] invalid policy name")
    try:
        resp = client.post("/simulate", json={
            "policy": "nonexistent_policy",
            "seq_len": 32,
            "n_facts": 4,
            "question_target": 2,
            "seed": 42
        })
        if resp.status_code == 400:
            print(f"  ✓ Status 400 - Rejected invalid policy")
            print(f"    Message: {resp.json().get('detail', 'N/A')[:80]}")
        else:
            print(f"  ✗ Unexpected status {resp.status_code}")
    except Exception as e:
        print(f"  ✗ Exception: {type(e).__name__}: {str(e)[:60]}")
    
    # Test 5: question_target >= n_facts
    print("\n[Test 5] question_target >= n_facts")
    try:
        resp = client.post("/simulate", json={
            "policy": "full_cache",
            "seq_len": 64,
            "n_facts": 4,
            "question_target": 5,  # >= n_facts
            "seed": 42
        })
        if resp.status_code == 400:
            print(f"  ✓ Status 400 - Rejected invalid question_target")
            print(f"    Message: {resp.json().get('detail', 'N/A')[:80]}")
        else:
            print(f"  ✗ Unexpected status {resp.status_code}")
    except Exception as e:
        print(f"  ✗ Exception: {type(e).__name__}: {str(e)[:60]}")
    
    # Test 6: Malformed request body (missing required field - policy has no default)
    print("\n[Test 6] completely empty request body")
    try:
        resp = client.post("/simulate", json={})
        if resp.status_code == 200:
            print(f"  ✓ Status 200 - All fields have defaults, accepted empty body")
        elif resp.status_code == 422:
            print(f"  ✓ Status 422 - Validation error")
            errors = resp.json().get('detail', [])
            if errors:
                print(f"    First error: {errors[0] if isinstance(errors, list) else str(errors)[:80]}")
        else:
            print(f"  ✗ Unexpected status {resp.status_code}")
    except Exception as e:
        print(f"  ✗ Exception: {type(e).__name__}: {str(e)[:60]}")
    
    # Test 7: Invalid field type
    print("\n[Test 7] invalid field type (seq_len as string)")
    try:
        resp = client.post("/simulate", json={
            "policy": "full_cache",
            "seq_len": "not_a_number",
            "n_facts": 4,
            "question_target": 2,
            "seed": 42
        })
        if resp.status_code == 422:
            print(f"  ✓ Status 422 - Type validation error")
        else:
            print(f"  ✗ Unexpected status {resp.status_code}")
    except Exception as e:
        print(f"  ✗ Exception: {type(e).__name__}: {str(e)[:60]}")
    
    # Test 8: Negative values
    print("\n[Test 8] negative seq_len")
    try:
        resp = client.post("/simulate", json={
            "policy": "full_cache",
            "seq_len": -10,
            "n_facts": 4,
            "question_target": 2,
            "seed": 42
        })
        if resp.status_code == 422:
            print(f"  ✓ Status 422 - Range validation error")
        else:
            print(f"  ✗ Unexpected status {resp.status_code}")
    except Exception as e:
        print(f"  ✗ Exception: {type(e).__name__}: {str(e)[:60]}")

def make_concurrent_request(request_id, policy, seq_len):
    """Make a single request and return timing info."""
    start = time.perf_counter()
    try:
        # Build request based on policy
        req_body = {
            "policy": policy,
            "seq_len": seq_len,
            "n_facts": 6,
            "question_target": 3,
            "seed": 42 + request_id,
        }
        
        # Add policy-specific parameters
        if policy == "heavy_hitter":
            req_body["budget"] = 32
        elif policy == "sliding_window":
            req_body["window_size"] = 32
            req_body["num_sink_tokens"] = 4
        elif policy == "bdh_inspired_state":
            req_body["state_size"] = 32
            req_body["decay"] = 0.995
        
        resp = client.post("/simulate", json=req_body)
        elapsed_ms = (time.perf_counter() - start) * 1000
        
        return {
            "request_id": request_id,
            "policy": policy,
            "status": resp.status_code,
            "elapsed_ms": elapsed_ms,
            "success": resp.status_code == 200
        }
    except Exception as e:
        elapsed_ms = (time.perf_counter() - start) * 1000
        return {
            "request_id": request_id,
            "policy": policy,
            "status": "exception",
            "elapsed_ms": elapsed_ms,
            "success": False,
            "error": str(e)[:100]
        }

def test_concurrent_requests():
    """Test concurrent requests to check if FastAPI handles them acceptably."""
    print("\n" + "=" * 70)
    print("CONCURRENT REQUEST TEST")
    print("=" * 70)
    
    policies = ["full_cache", "sliding_window", "heavy_hitter", "bdh_inspired_state"]
    num_requests = 3  # Small demo - 3 concurrent requests
    
    print(f"\nSending {num_requests} concurrent requests per policy...")
    
    for policy in policies:
        print(f"\n[{policy}]")
        start = time.perf_counter()
        
        with ThreadPoolExecutor(max_workers=num_requests) as executor:
            futures = [
                executor.submit(make_concurrent_request, i, policy, 64)
                for i in range(num_requests)
            ]
            
            results = []
            for future in as_completed(futures):
                result = future.result()
                results.append(result)
        
        total_elapsed = (time.perf_counter() - start) * 1000
        
        # Analyze results
        successes = sum(1 for r in results if r["success"])
        avg_response_time = sum(r["elapsed_ms"] for r in results) / len(results)
        max_response_time = max(r["elapsed_ms"] for r in results)
        
        print(f"  Total wall time: {total_elapsed:.1f} ms")
        print(f"  Successes: {successes}/{num_requests}")
        print(f"  Avg response time: {avg_response_time:.1f} ms")
        print(f"  Max response time: {max_response_time:.1f} ms")
        
        if successes == num_requests:
            if total_elapsed < num_requests * 1000:
                print(f"  ✓ All succeeded, acceptable concurrency handling")
            else:
                print(f"  ⚠ All succeeded but took longer than expected")
        else:
            print(f"  ✗ Some requests failed")
            for r in results:
                if not r["success"]:
                    print(f"    Request {r['request_id']}: {r.get('error', r['status'])}")

def main():
    print("=" * 70)
    print("STRESS TEST FOR /simulate ENDPOINT")
    print("=" * 70)
    
    # Test edge cases
    test_edge_cases()
    
    # Test concurrent requests
    test_concurrent_requests()
    
    print("\n" + "=" * 70)
    print("STRESS TEST COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    main()
