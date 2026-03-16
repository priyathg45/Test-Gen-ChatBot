import requests
import json

URL = "http://localhost:5000/chat"
headers = {"Content-Type": "application/json"}
payload = {
    "message": "can you explain what this attached document says?",
    "session_id": "test_session_123"
}

print("Sending request to Chatbot...")
try:
    response = requests.post(URL, json=payload, headers=headers)
    print("Status Code:", response.status_code)
    try:
        data = response.json()
        print("Response JSON:\n", json.dumps(data, indent=2))
        
        # Check if products were retrieved
        if data.get("retrieved_products"):
            print("\nWARNING: Chatbot returned products for a document query!")
        else:
            print("\nSUCCESS: No products returned for document query.")
    except Exception as e:
        print("Failed to parse JSON:", response.text)
except requests.exceptions.RequestException as e:
    print("Connection error:", e)
