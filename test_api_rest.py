import json
import requests

try:
    with open('app_settings.json', 'r') as f:
        data = json.load(f)
    keys = data.get('api_keys', [])
    valid_keys = [k.strip() for k in keys if k.strip()]
    if not valid_keys:
        print("No keys found.")
        exit()
        
    key = valid_keys[0]
    print(f"Testing REST API with key ending in: {key[-4:]}")
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-pro-preview:generateContent?key={key}"
    payload = {"contents": [{"parts": [{"text": "Hello, are you online?"}]}]}
    
    # 3.1 PRO TEST
    print("Testing 3.1 Pro...")
    r1 = requests.post(url, headers={'Content-Type':'application/json'}, json=payload, timeout=20)
    print(f"3.1 PRO STATUS: {r1.status_code}")
    if r1.status_code != 200:
        print(f"3.1 ERROR MSG: {r1.text[:200]}")
    else:
        print("3.1 PRO SUCCESS")
        
    # 3.0 PRO TEST
    url2 = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.0-pro:generateContent?key={key}"
    print("\nTesting 3.0 Pro...")
    r2 = requests.post(url2, headers={'Content-Type':'application/json'}, json=payload, timeout=20)
    print(f"3.0 PRO STATUS: {r2.status_code}")
    if r2.status_code != 200:
        print(f"3.0 ERROR MSG: {r2.text[:200]}")
    else:
        print("3.0 PRO SUCCESS")
    
except Exception as e:
    print(f"Script Error: {e}")
