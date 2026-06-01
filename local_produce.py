from agents import OracleBrain

from memory import MemoryManager

mm = MemoryManager()
settings = mm.load_settings()
keys = settings.get('api_keys', [])

brain = OracleBrain(api_keys=keys)
order_note = """
House built in 1887.
Living here 54 years from Sept 1972, aged 12, with parents & 2 brothers. Brothers left home. I lived with parents, they passed. Downstairs living room,dining rm, kitchen, toilet, garden door. Upstairs bathroom, 3 bedrooms. 
"""
reading_topic = "House Psychic Reading & Energy Scan | Complete Home Purification | Banish Stagnant Energy - Blocks | Deep Space Clearing"
client_email = "fatsy2k@yahoo.co.uk"
target_length = "Extremely Long, Deep, and Detailed (Minimum 4 Pages of Esoteric Depth, roughly 2500+ words)"

def progress(msg):
    print(f"[STATUS] {msg}", flush=True)

print("--- STARTING LOCAL PRODUCTION ---", flush=True)
reading_text, delivery_msg, usage_stats, audio_path = brain.run_cycle(
    order_note=order_note,
    reading_topic=reading_topic,
    client_email=client_email,
    target_length=target_length,
    generate_audio=False,
    progress_callback=progress
)

print("\n--- DONE. SAVING HTML ---", flush=True)

html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Sovereign Home Purification - {client_email}</title>
    <style>
        body {{
            background-color: #0a0a0a;
            color: #d4af37;
            font-family: 'Georgia', serif;
            padding: 40px 20px;
            line-height: 1.8;
            margin: 0;
        }}
        .container {{
            max-width: 900px;
            margin: 0 auto;
            background: #111;
            padding: 50px;
            border: 1px solid #332a0d;
            box-shadow: 0 0 30px rgba(212, 175, 55, 0.1);
        }}
        h1 {{
            text-align: center;
            border-bottom: 2px solid #55441a;
            padding-bottom: 30px;
            margin-bottom: 40px;
            font-size: 2em;
            letter-spacing: 2px;
            text-transform: uppercase;
        }}
        .reading-text {{
            white-space: pre-wrap;
            font-size: 1.15em;
            text-align: justify;
        }}
        .delivery-msg {{
            margin-top: 60px;
            padding-top: 20px;
            border-top: 1px dashed #55441a;
            text-align: center;
            font-style: italic;
            color: #a0a0a0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Sovereign Reading:<br><span style="font-size: 0.6em; color: #888;">House Psychic Reading & Energy Scan</span></h1>
        
        <div class="reading-text">{reading_text.replace('\n', '<br>')}</div>
        
        <div class="delivery-msg">
            {delivery_msg.replace('\n', '<br>')}
        </div>
    </div>
</body>
</html>
"""

with open("reading_fatsy2k.html", "w", encoding="utf-8") as f:
    f.write(html_content)

print(f"Saved to reading_fatsy2k.html. Length: {len(reading_text)} characters", flush=True)
