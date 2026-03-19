import requests
import json

BASE_URL = "http://localhost:5000"
SESSION_ID = "test_doc_session_999"

print("1. Uploading temporary test document...")
files = {'file': ('test.txt', b'This is a fake PDF about llamas. They are cool.')}
data = {'session_id': SESSION_ID}
res_upload = requests.post(f"{BASE_URL}/upload", files=files, data=data)
print("Upload status:", res_upload.status_code)

print("\n2. Sending document-related chat query...")
payload = {
    "message": "can you explain what this text says?",
    "session_id": SESSION_ID
}
res_chat = requests.post(f"{BASE_URL}/chat", json=payload)
print("Chat status:", res_chat.status_code)
try:
    data = res_chat.json()
    print("Response JSON:\n", json.dumps(data, indent=2))
    
    if data.get("retrieved_products"):
        print("\nFAIL: Products returned despite a document being uploaded!")
    else:
        print("\nPASS: No products appended! The query correctly focused only on the document.")
        
except Exception as e:
    print("Error parsing chat response:", res_chat.text)
