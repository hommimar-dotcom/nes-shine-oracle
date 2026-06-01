import sys
from memory import MemoryManager

raw_keys = [
    "AIzaSyB5ulW2raqhu99toKkQ8m0nHTTPaeVH2oc",
    "AIzaSyCzIpwdLfgprJtx55eHmX27Zs6e2xIze5U",
    "AIzaSyAkud3Kr5JNMpcrTbCEjdfsRtUG4hiK8yM",
    "AIzaSyDIpoyk-kEbvciXjHmh41JtuF5Z-aXQyt0",
    "AIzaSyCzIpwdLfgprJtx55eHmX27Zs6e2xIze5U",
    "AIzaSyA-pCkCXoelcllisGuifZ9OkWJR8P_mUZ8",
    "AIzaSyA8kenp5d05MUWu2tkY67Mb73SX82DKtuY",
    "AIzaSyC5cUxsbKNZQeqqTW9hFVP_fm_ldgghz2Q",
    "AIzaSyBC2lGVqWAL9kdteiutj-qUeHtm2jOoVEc",
    "AIzaSyAk8pMHYm7MKOQdL6yfmyc3to8v8S9N_08",
    "AIzaSyAjuGuLmR9AOjYhXIzJXk8jeGziLLEj_Jg",
    "AIzaSyDA2zrTrbdKPYE6Bl0W78UnfWIYmAFenpY",
    "AIzaSyDuccMb9CFzYykbSCAgKsGcHg_1kduMWHk",
    "AIzaSyB5ulW2raqhu99toKkQ8m0nHTTPaeVH2oc",
    "AIzaSyAZRoEk_NefdFIqAWlRtAdxdcg4pHfZlYc",
    "AIzaSyDIpoyk-kEbvciXjHmh41JtuF5Z-aXQyt0"
]

unique_keys = []
for k in raw_keys:
    k = k.strip()
    if k and k not in unique_keys:
        unique_keys.append(k)

print(f"Extracted {len(unique_keys)} UNIQUE keys from the provided 16.")

mm = MemoryManager()
settings = mm.load_settings()
settings["api_keys"] = unique_keys
success = mm.save_settings(settings)

if success:
    print(f"SUCCESS: System injected {len(unique_keys)} API keys into memory.")
else:
    print("FAILED: Could not write to memory manager.")
