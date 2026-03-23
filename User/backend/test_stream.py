import requests
import json
import sys

url = "http://localhost:5000/chat/stream"
data = {"message": "hi"}

print(f"Testing streaming endpoint at {url}...")
try:
    # Use stream=True to process chunks
    response = requests.post(url, json=data, stream=True, timeout=30)
    response.raise_for_status()
    
    print("Connection established. Reading stream...\n")
    for line in response.iter_lines():
        if line:
            decoded_line = line.decode('utf-8')
            print(f"CHUNK: {decoded_line}")
            if "[DONE]" in decoded_line:
                print("\nStream finished successfully.")
                break
except Exception as e:
    print(f"\nError occurred: {e}")
    sys.exit(1)
