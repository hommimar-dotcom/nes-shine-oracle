"""
Audio Service for Nes Shine Oracle
Converts approved reading text (HTML) into speech-ready text,
then generates audio via ElevenLabs.
"""

import os
import re
from html.parser import HTMLParser


class HTMLStripper(HTMLParser):
    """Strips HTML tags and converts structure into speech-friendly text."""

    def __init__(self):
        super().__init__()
        self.result = []
        self._current_tag = None
        self._skip_tags = {"style", "script"}
        self._skip = False

    def handle_starttag(self, tag, attrs):
        self._current_tag = tag
        classes = dict(attrs).get("class", "")

        if tag in self._skip_tags:
            self._skip = True
            return

        # Section breaks: deep breath before new sections
        if tag == "h1":
            self.result.append("\n\n")
        elif tag == "h2":
            self.result.append("\n\n...\n\n")

        # Chant block: add a reverent pause before mantras
        if "chantblock" in classes:
            self.result.append("\n\n...\n\n")

        # Highlight box: slight pause to emphasize
        if "highlightbox" in classes:
            self.result.append("\n...\n")

    def handle_endtag(self, tag):
        if tag in self._skip_tags:
            self._skip = False
            return

        if tag == "p":
            self.result.append("\n\n")
        elif tag == "h1":
            self.result.append(".\n\n")
        elif tag == "h2":
            self.result.append(".\n\n")

        # Closing highlight box
        if tag == "div":
            pass  # handled naturally by paragraph endings

        self._current_tag = None

    def handle_data(self, data):
        if self._skip:
            return
        # Skip the signature, archive footer, and session ID lines
        if self._current_tag in self._skip_tags:
            return
        text = data.strip()
        if text:
            self.result.append(text + " ")

    def get_text(self):
        return "".join(self.result).strip()


def strip_html(html_text):
    """Remove all HTML tags and return clean text with speech pauses."""
    stripper = HTMLStripper()
    stripper.feed(html_text)
    text = stripper.get_text()

    # Remove the signature line and archive footer
    text = re.sub(r"Nes Shine\s*SESSION ID.*$", "", text, flags=re.DOTALL)

    # Clean up excessive whitespace/newlines
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)

    return text.strip()


def prepare_for_speech(clean_text):
    """
    Final pass: make the stripped text sound natural when spoken.
    Adds subtle pauses (ellipses) at paragraph boundaries.
    Does NOT alter content, word choice, or persona.
    """
    lines = clean_text.split("\n\n")
    processed = []

    for line in lines:
        line = line.strip()
        if not line:
            continue
        processed.append(line)

    # Join with a breath pause between paragraphs
    return "\n\n".join(processed)


class AudioService:
    """Handles ElevenLabs TTS generation for approved readings."""

    def __init__(self, api_key=None, voice_id=None):
        self.api_key = api_key or os.environ.get("ELEVENLABS_API_KEY")
        if not self.api_key:
            raise ValueError("ELEVENLABS_API_KEY not set.")

        from elevenlabs.client import ElevenLabs
        self.client = ElevenLabs(api_key=self.api_key)

        self.voice_id = voice_id or os.environ.get("ELEVENLABS_VOICE_ID", "")
        if not self.voice_id:
            raise ValueError("ELEVENLABS_VOICE_ID not set.")

        self.model = "eleven_turbo_v2_5"

    def generate_audio(self, html_text, output_filename="reading.mp3"):
        """
        Takes raw HTML reading text, strips it, prepares for speech,
        and generates an MP3 via ElevenLabs.

        Returns the file path on success, None on failure.
        """
        from elevenlabs import save

        # Step 1: Strip HTML
        clean = strip_html(html_text)

        # Step 2: Prepare for speech
        speech_text = prepare_for_speech(clean)

        if not speech_text or len(speech_text) < 100:
            print("AUDIO WARNING: Text too short for audio generation.")
            return None

        print(f"AUDIO: Generating audio for {len(speech_text)} characters...")

        try:
            audio_generator = self.client.generate(
                text=speech_text,
                voice=self.voice_id,
                model=self.model,
            )

            save_dir = "saved_audio"
            os.makedirs(save_dir, exist_ok=True)
            filepath = os.path.join(save_dir, output_filename)

            save(audio_generator, filepath)
            print(f"AUDIO: Saved to {filepath}")
            return filepath

        except Exception as e:
            print(f"AUDIO ERROR: {e}")
            return None
