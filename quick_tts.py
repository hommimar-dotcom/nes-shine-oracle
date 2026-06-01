import os
import requests
import json
import uuid

# ========================================================
# NES SHINE - STANDALONE ELEVENLABS AUDIO GENERATOR
# ========================================================

# Settings
API_KEY = os.environ.get("ELEVENLABS_API_KEY", "")  # Put your API key here if not in env
VOICE_ID = os.environ.get("ELEVENLABS_VOICE_ID", "") # Put your Voice ID here if not in env

# ElevenLabs Parameters (Tuned for Nes Shine / Veronica style)
MODEL_ID = "eleven_multilingual_v2" # Recommended for high quality emotional depth
STABILITY = 0.35      # Lower for more emotional range
SIMILARITY = 0.85     # Higher to stick closely to the original voice clone
STYLE = 0.0           # Keep at 0 to avoid exaggeration
USE_SPEAKER_BOOST = True

def generate_voice(text, output_filename="output.mp3"):
    """Generates audio from text using ElevenLabs API and saves it to a file."""
    
    if not API_KEY or not VOICE_ID:
        print("ERROR: Missing API_KEY or VOICE_ID.")
        print("Please set them in this script or as environment variables.")
        return False

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
    
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": API_KEY
    }
    
    data = {
        "text": text,
        "model_id": MODEL_ID,
        "voice_settings": {
            "stability": STABILITY,
            "similarity_boost": SIMILARITY,
            "style": STYLE,
            "use_speaker_boost": USE_SPEAKER_BOOST
        }
    }
    
    print(f"Generating audio to '{output_filename}'...")
    print(f"Length: {len(text)} characters.")
    
    try:
        response = requests.post(url, json=data, headers=headers)
        
        if response.status_code == 200:
            with open(output_filename, 'wb') as f:
                f.write(response.content)
            print(f"✅ SUCCESS! Audio saved to: {output_filename}")
            return True
        else:
            print(f"❌ ERROR: ElevenLabs API returned status code {response.status_code}")
            try:
                error_data = response.json()
                print(f"Details: {json.dumps(error_data, indent=2)}")
            except:
                print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ EXCEPTION: {str(e)}")
        return False

if __name__ == "__main__":
    print("\n" + "="*50)
    print("NES SHINE - QUICK TTS GENERATOR")
    print("="*50 + "\n")
    
    input_text = input("Paste your text here (Press Enter to generate):\n> ")
    
    if input_text.strip():
        # Generate a unique filename based on the first few words
        safe_words = "".join(x for x in input_text[:15] if x.isalnum() or x.isspace()).strip().replace(" ", "_").lower()
        if not safe_words: 
            safe_words = "audio"
        
        filename = f"saved_audio/direct_generate_{safe_words}_{str(uuid.uuid4())[:4]}.mp3"
        
        # Ensure directory exists
        os.makedirs("saved_audio", exist_ok=True)
        
        generate_voice(input_text, filename)
    else:
        print("No text provided. Exiting.")
