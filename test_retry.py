import google.generativeai as genai
from google.api_core import retry

try:
    genai.configure(api_key="TEST")
    model = genai.GenerativeModel("gemini-3.1-pro-preview")
    # check if retry is accepted
    model.generate_content("hello", request_options={"timeout": 5, "retry": retry.Retry(deadline=5)})
    print("Accepted!")
except Exception as e:
    print(f"Failed: {type(e).__name__} - {e}")
