import sys
import json
import requests
from memory import MemoryManager

sys.stdout.reconfigure(encoding='utf-8')

print("--- EXHAUSTIVE RAW API INVESTIGATION ---")

mm = MemoryManager()
settings = mm.load_settings()
keys = settings.get('api_keys', [])

if not keys:
    print("NO KEYS FOUND")
    sys.exit(0)

print(f"Testing {len(keys)} registered keys directly via REST HTTP...\n")

# Use the exact production model hitting 429
model_endpoint = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-pro-preview:generateContent"
payload = {"contents": [{"parts": [{"text": "ping"}]}]}

for i, key in enumerate(keys):
    masked = f"{key[:8]}...{key[-4:]}" if len(key) > 15 else "INVALID_LENGTH"
    
    url = f"{model_endpoint}?key={key}"
    try:
        response = requests.post(url, json=payload, headers={'Content-Type': 'application/json'}, timeout=10)
        
        status = response.status_code
        if status == 200:
            print(f"Key {i+1} ({masked}): SUCCESS (200 OK)")
        else:
            print(f"Key {i+1} ({masked}): FAILED ({status})")
            
            try:
                error_data = response.json()
                error_details = error_data.get('error', {})
                code = error_details.get('code', 'N/A')
                msg = error_details.get('message', 'No message provided')
                reason = error_details.get('status', 'N/A')
                
                print(f"  -> Reason : {reason}")
                print(f"  -> Code   : {code}")
                print(f"  -> Message: {msg}")
            except:
                print(f"  -> Raw response: {response.text[:200]}")
                
    except Exception as e:
        print(f"Key {i+1} ({masked}): CONNECTION ERROR - {str(e)}")
        
    print("-" * 40)
