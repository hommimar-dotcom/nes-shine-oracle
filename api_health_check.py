import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

api_key = os.environ.get("GEMINI_KEY_1")
if not api_key:
    print("NO API KEY FOUND")
    exit(1)

genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-3.1-pro-preview")

print("Sending test request to gemini-3.1-pro-preview...")
try:
    response = model.generate_content("Hello, respond with 'API IS ALIVE'")
    print(f"SUCCESS: {response.text}")
except Exception as e:
    print(f"FAILED: {e}")
