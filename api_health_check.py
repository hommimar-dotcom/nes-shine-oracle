"""
Nes Shine Oracle — Full API Health Check
Pulls keys from Supabase (same source as the app) and tests all models.
"""
import os
import time
import json
import google.generativeai as genai

# Try to load from Supabase (same as the real app)
keys = []

try:
    from supabase import create_client
    url = os.environ.get("SUPABASE_URL", "")
    key = os.environ.get("SUPABASE_KEY", "")
    
    if url and key:
        sb = create_client(url, key)
        result = sb.table("client_memories").select("sessions").eq("client_key", "__app_settings__").execute()
        if result.data:
            sessions = result.data[0]["sessions"]
            settings = json.loads(sessions) if isinstance(sessions, str) else sessions
            keys = [k.strip() for k in settings.get("api_keys", []) if k.strip()]
            print(f"[SUPABASE] {len(keys)} key bulundu")
    else:
        print("[SUPABASE] URL/KEY env vars yok")
except Exception as e:
    print(f"[SUPABASE HATA] {e}")

# Fallback: local app_settings.json
if not keys and os.path.exists("app_settings.json"):
    try:
        with open("app_settings.json", "r") as f:
            settings = json.load(f)
            keys = [k.strip() for k in settings.get("api_keys", []) if k.strip()]
            print(f"[LOCAL FILE] {len(keys)} key bulundu")
    except:
        pass

# Fallback: env vars
if not keys:
    for i in range(1, 10):
        k = os.environ.get(f"GEMINI_KEY_{i}")
        if k:
            keys.append(k)
    if keys:
        print(f"[ENV VARS] {len(keys)} key bulundu")

if not keys:
    print("\n❌ HİÇBİR KAYNAK'TAN API KEY BULUNAMADI!")
    print("   - Supabase env vars (SUPABASE_URL, SUPABASE_KEY) ayarli mi?")
    print("   - app_settings.json mevcut mu?")
    print("   - GEMINI_KEY_1 env var ayarli mi?")
    exit(1)

print(f"\n{'='*60}")
print(f"  NES SHINE API HEALTH CHECK")
print(f"  Toplam {len(keys)} anahtar test edilecek")
print(f"{'='*60}")

models_to_test = [
    ("gemini-3.1-pro-preview", "PRIMARY (Spell + Oracle)"),
    ("gemini-3-pro-preview", "FALLBACK (Spell Engine)"),
    ("gemini-2.0-flash", "FAST (Backup)"),
]

for i, api_key in enumerate(keys):
    masked = f"{api_key[:8]}...{api_key[-4:]}"
    print(f"\n{'─'*50}")
    print(f"  KEY {i+1}/{len(keys)}: {masked}")
    print(f"{'─'*50}")
    
    genai.configure(api_key=api_key)
    
    for model_name, label in models_to_test:
        try:
            model = genai.GenerativeModel(model_name)
            start = time.time()
            response = model.generate_content(
                "Say 'OK' in one word only.",
                request_options={'timeout': 30}
            )
            elapsed = time.time() - start
            
            if response and response.text:
                print(f"  ✅ {label}: ÇALIŞIYOR ({elapsed:.1f}s)")
            else:
                print(f"  ⚠️ {label}: BOŞ YANIT")
        except Exception as e:
            err_name = type(e).__name__
            err_msg = str(e)[:100]
            if "429" in err_msg or "ResourceExhausted" in err_name:
                print(f"  ❌ {label}: KOTA DOLU (429 Rate Limit)")
            elif "DeadlineExceeded" in err_name:
                print(f"  ⏳ {label}: TIMEOUT (30s — Google sunucu yoğun)")
            elif "not found" in err_msg.lower() or "InvalidArgument" in err_name:
                print(f"  ❌ {label}: MODEL GEÇERSİZ ({model_name})")
            else:
                print(f"  ❌ {label}: {err_name} — {err_msg}")

print(f"\n{'='*60}")
print(f"  TEST TAMAMLANDI — {time.strftime('%H:%M:%S')}")
print(f"{'='*60}")
