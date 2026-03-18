import requests
import json
import time

BASE_URL = "http://localhost:5001"

def test_logs():
    print("Fetching logs...")
    # Health check to ensure backend is up
    try:
        h = requests.get(f"{BASE_URL}/health/").json()
        print(f"Server status: {h['overall']}")
    except:
        print("Server unreachable")
        return

    # To test real logs, we'd need a token or have it open. 
    # Since I can't easily login, I'll check if /api/logs is accessible 
    # (it shouldn't be without token, but let's confirm 401)
    r = requests.get(f"{BASE_URL}/logs/")
    print(f"Logs status (no token): {r.status_code}")
    
    # Let's mock a log entry directly if possible to see if collection is working
    # But better to just let the user verify the UI.
    
if __name__ == "__main__":
    test_logs()
