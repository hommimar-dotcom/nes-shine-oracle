import os
import google.generativeai as genai

genai.configure(api_key=os.environ.get("GEMINI_KEY_1"))
model = genai.GenerativeModel("gemini-3.1-pro-preview")
print("Generating...")
response = model.generate_content("Can you write a 500 word story?", request_options={"timeout": 60})
print("Done:", response.text)
