import json
import google.generativeai as genai

def test_streaming_metadata():
    try:
        with open('app_settings.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        keys = data.get('api_keys', [])
        if not keys:
            print("No keys found.")
            return
            
        genai.configure(api_key=keys[0])
        model = genai.GenerativeModel('gemini-3.1-pro-preview')
        
        print("--- TESTING STREAMING BILLING METADATA ---")
        response = model.generate_content("Bir falcı gibi bana kısaca merhaba de.", stream=True)
        
        for chunk in response:
            pass
            
        print("Stream completed.")
        
        meta = getattr(response, 'usage_metadata', None)
        if meta:
            print(f"[SUCCESS] Usage metadata found on response object: {meta}")
        else:
            print("[FAILED] Usage metadata IS NOT present on the root response object after streaming!")
            
        # Let's see if it's on the last chunk
        try:
            last_chunk_meta = getattr(chunk, 'usage_metadata', None)
            if last_chunk_meta:
                print(f"[FOUND ON CHUNK] usage_metadata is actually on the last chunk: {last_chunk_meta}")
        except:
            pass

    except Exception as e:
        print("Error:", str(e))

if __name__ == "__main__":
    test_streaming_metadata()
