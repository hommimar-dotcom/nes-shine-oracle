import requests
import sys

key = "AIzaSyCeMSFms2OTjQn9PXmDfdhEfPb44SzXKnQ"
url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-pro-preview:generateContent?key={key}"
payload = {"contents": [{"parts": [{"text": "ping"}]}]}

try:
    response = requests.post(url, json=payload, headers={'Content-Type': 'application/json'}, timeout=15)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
