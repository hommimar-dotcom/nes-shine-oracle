"""List all available models for this API key"""
import os, json
import google.generativeai as genai

# Load key
keys = []
if os.path.exists("app_settings.json"):
    with open("app_settings.json", "r") as f:
        settings = json.load(f)
        keys = [k.strip() for k in settings.get("api_keys", []) if k.strip()]

if keys:
    genai.configure(api_key=keys[0])
    print(f"Key: {keys[0][:8]}...{keys[0][-4:]}\n")
    print("Available models with 'generateContent' support:\n")
    for m in genai.list_models():
        if "generateContent" in [method.name for method in m.supported_generation_methods]:
            print(f"  {m.name}")
else:
    print("No keys found")
