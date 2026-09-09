"""
Quick integration test - verify frontend can talk to backend.
Tests both /health and /simulate endpoints.
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_health():
    """Test /health endpoint."""
    print("Testing /health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"  Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"  ✓ Backend is alive!")
            print(f"  Model state: {data.get('model_state', 'unknown')}")
            print(f"  Vocab size: {data.get('vocab_size', 'unknown')}")
            return True
        else:
            print(f"  ✗ Unexpected status code")
            return False
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False

def test_simulate():
    """Test /simulate endpoint with a simple request."""
    print("\nTesting /simulate endpoint...")
    try:
        # Simple test request
        payload = {
            "policy": "full_cache",
            "seq_len": 64,
            "n_facts": 4,
            "question_target": 2,
            "seed": 42
        }
        
        print(f"  Sending request: policy={payload['policy']}, seq_len={payload['seq_len']}")
        response = requests.post(f"{BASE_URL}/simulate", json=payload)
        print(f"  Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            sim = data.get('simulation', {})
            episode = data.get('episode', {})
            
            print(f"  ✓ Simulation completed!")
            print(f"  Steps: {len(sim.get('steps', []))}")
            print(f"  Final answer: {sim.get('final_answer', 'N/A')}")
            print(f"  Ground truth: {sim.get('ground_truth', 'N/A')}")
            print(f"  Correct: {sim.get('correct', False)}")
            print(f"  Episode text length: {len(episode.get('text', ''))}")
            return True
        else:
            print(f"  ✗ Status code: {response.status_code}")
            print(f"  Response: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False

def main():
    print("=" * 70)
    print("CacheQuake Integration Test")
    print("=" * 70)
    
    health_ok = test_health()
    simulate_ok = test_simulate()
    
    print("\n" + "=" * 70)
    if health_ok and simulate_ok:
        print("✓ INTEGRATION TEST PASSED")
        print("\nBoth servers are running and communicating correctly!")
        print("\nYou can now open your browser to:")
        print("  Frontend: http://localhost:5173")
        print("  Backend:  http://localhost:8000/docs (API documentation)")
    else:
        print("✗ INTEGRATION TEST FAILED")
        if not health_ok:
            print("  - /health endpoint failed")
        if not simulate_ok:
            print("  - /simulate endpoint failed")
    print("=" * 70)

if __name__ == "__main__":
    main()
