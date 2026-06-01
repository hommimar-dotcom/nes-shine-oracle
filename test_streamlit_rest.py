import streamlit as st
from memory import MemoryManager
import requests

try:
    mm = MemoryManager()
    keys = mm.load_settings().get('api_keys', [])
    valid_keys = [k.strip() for k in keys if k.strip()]
    if not valid_keys:
        st.write("No keys found.")
    else:
        key = valid_keys[0]
        st.write(f"Testing REST API with key ending in: {key[-4:]}")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-pro-preview:generateContent?key={key}"
        payload = {"contents": [{"parts": [{"text": "Hello, are you online?"}]}]}
        
        st.write("Testing 3.1 Pro...")
        r1 = requests.post(url, headers={'Content-Type':'application/json'}, json=payload, timeout=20)
        st.write(f"3.1 PRO STATUS: {r1.status_code}")
        if r1.status_code != 200:
            st.write(f"3.1 ERROR MSG: {r1.text[:200]}")
        else:
            st.write("3.1 PRO SUCCESS")
            
        url2 = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.0-pro:generateContent?key={key}"
        st.write("\nTesting 3.0 Pro...")
        r2 = requests.post(url2, headers={'Content-Type':'application/json'}, json=payload, timeout=20)
        st.write(f"3.0 PRO STATUS: {r2.status_code}")
        if r2.status_code != 200:
            st.write(f"3.0 ERROR MSG: {r2.text[:200]}")
        else:
            st.write("3.0 PRO SUCCESS")
        
        # MASSIVE PROMPT TEST ON 3.1
        st.write("\nTesting Massive Prompt on 3.1 Pro...")
        massive_payload = {"contents": [{"parts": [{"text": "Write a 15000 character epic story about magic and occultism. " * 50}]}]}
        r3 = requests.post(url, headers={'Content-Type':'application/json'}, json=massive_payload, timeout=60)
        st.write(f"3.1 MASSIVE PROMPT STATUS: {r3.status_code}")
        if r3.status_code != 200:
            st.write(f"3.1 MASSIVE ERROR MSG: {r3.text[:200]}")
        else:
            st.write("3.1 MASSIVE SUCCESS")
            
except Exception as e:
    st.write(f"Script Error: {e}")

st.write("TEST COMPLETE")
