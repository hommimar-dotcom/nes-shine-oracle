import os
from elevenlabs.client import ElevenLabs
import json

def generate_nes_shine_voice():
    api_key = os.environ.get("ELEVENLABS_API_KEY")
    if not api_key:
        print("ERROR: ELEVENLABS_API_KEY environment variable not found.")
        return

    client = ElevenLabs(api_key=api_key)

    # 1. Voice Design Parameters
    print("Generating voice design...")
    design_response = client.voice_generation.generate(
        gender="female",
        accent="british",
        age="middle_aged",
        accent_strength=1.5,
        text="Listen to me carefully. I am the Oracle. The path you walk is shadowed, but I see the threads. Breathe in the silence.",
    )
    
    # 2. Save the design and create the Voice ID
    print("Voice design generated. Creating permanent Voice ID...")
    try:
        voice = client.voice_generation.create_a_previously_generated_voice(
            voice_name="Nes Shine Oracle",
            voice_description="Mystic, authoritative, whispering, slow cadence.",
            generated_voice_id=design_response.voice_id
        )
        print(f"✅ Nes Shine Voice Created Successfully!")
        print(f"Voice ID: {voice.voice_id}")
        
    except Exception as e:
         print(f"Failed to save voice: {e}")

if __name__ == "__main__":
    generate_nes_shine_voice()
