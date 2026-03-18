import requests
import json

BASE_URL = "http://localhost:5001"

def test_endpoint(path):
    print(f"\nTesting {path}...")
    try:
        # We need a token. Let's see if we can get one or bypass auth for testing if we run locally.
        # Since I can't easily get a token without login, I'll just check the health endpoint which I might have put behind auth.
        # Wait, I did put it behind auth in the blueprint? No, I didn't add check_admin_auth to health_check in health.py
        
        response = requests.get(f"{BASE_URL}{path}")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_endpoint("/health/")
    # For others, we'd need a token.
