import sys
import google.generativeai as genai
from memory import MemoryManager
from google.generativeai.types import HarmCategory, HarmBlockThreshold

# Ensure UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')

print("--- 3.1 PRO API KEY DIAGNOSTICS ---")

# Load keys
mm = MemoryManager()
keys = mm.load_settings().get('api_keys', [])

print(f"Testing {len(keys)} keys...\n")

if not keys:
    print("NO KEYS FOUND IN APP_SETTINGS.JSON")
    sys.exit(0)

# The production safety settings
safety_settings = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
}

for i, k in enumerate(keys):
    masked_key = f"{k[:10]}..." if len(k) > 10 else "INVALID"
    try:
        genai.configure(api_key=k)
        model = genai.GenerativeModel(
            model_name='gemini-3.1-pro-preview',
            safety_settings=safety_settings
        )
        response = model.generate_content("Ping. Reply 'Pong' if active.")
        print(f"Key {i+1} ({masked_key}): SUCCESS - Active for gemini-3.1-pro-preview")
    except Exception as e:
        error_name = type(e).__name__
        error_msg = str(e).split('\n')[0] # Only get first line of error
        print(f"Key {i+1} ({masked_key}): FAILED - {error_name}")
        print(f"  -> {error_msg}")

print("\n--- DIAGNOSTICS COMPLETE ---")
