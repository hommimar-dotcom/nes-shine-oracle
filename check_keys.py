import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

keys = []
for i in range(1, 10):
    k = os.environ.get(f"GEMINI_KEY_{i}")
    if k:
        keys.append(k)

print(f"Buldunan Anahtar Sayısı: {len(keys)}")

for i, key in enumerate(keys):
    try:
        genai.configure(api_key=key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content("Hello! Say Hi.")
        if response.text:
            print(f"API Key {i+1}: AKTİF VE ÇALIŞIYOR (Yanıt: {response.text.strip()})")
    except Exception as e:
        err = str(e)
        if "429" in err or "ResourceExhausted" in type(e).__name__:
            print(f"API Key {i+1}: KOTA DOLU (Rate Limit / Exhausted) ❌")
        else:
            print(f"API Key {i+1}: HATA ❌ - {err}")
