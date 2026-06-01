import json
import traceback
import google.generativeai as genai

try:
    with open('app_settings.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    keys = data.get('api_keys', [])
    valid_keys = [k.strip() for k in keys if k.strip()]
    
    print(f"Loaded {len(valid_keys)} valid keys.")
    if not valid_keys:
        print("No valid keys found.")
        exit(1)
        
    print(f"Testing the first key: {valid_keys[0][:10]}...")
    genai.configure(api_key=valid_keys[0])
    
    print("Fetching models...")
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"- {m.name}")
    
    print("Testing gemini-2.5-pro...")
    model25 = genai.GenerativeModel('gemini-2.5-pro')
    res25 = model25.generate_content('Hello')
    print("Model 2.5 response:", res25.text)
    
    print("Testing gemini-3.1-pro-preview...")
    model31 = genai.GenerativeModel('gemini-3.1-pro-preview')
    res = model31.generate_content('Hello')
    print("Response:", res.text)
    
except Exception as e:
    print("\n--- ERROR ---")
    print(type(e).__name__)
    print(e)
    traceback.print_exc()
