import requests
import json
import uuid
import sys

API_URL = "http://localhost:5000"
session_id = f"test_{uuid.uuid4().hex}"

def test_upload():
    print(f"Testing upload for session: {session_id}")
    files = {
        'file': ('dummy.pdf', open('dummy.pdf', 'rb'), 'application/pdf')
    }
    data = {
        'session_id': session_id
    }
    
    try:
        response = requests.post(f"{API_URL}/upload", files=files, data=data)
        print(f"Status: {response.status_code}")
        result = response.json()
        print(json.dumps(result, indent=2))
        
        if result.get('success'):
            print("\nTesting chat intent...")
            chat_data = {
                'session_id': session_id,
                'message': 'summerize given pdf'
            }
            chat_response = requests.post(f"{API_URL}/chat", json=chat_data)
            print(f"Chat status: {chat_response.status_code}")
            print(json.dumps(chat_response.json(), indent=2))
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_upload()
