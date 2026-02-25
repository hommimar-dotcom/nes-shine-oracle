"""
Audio Service for Nes Shine Oracle
Converts approved reading text (HTML) into speech-ready text,
then generates audio via ElevenLabs with chunking and cost tracking.
"""

import os
import re
import io
from html.parser import HTMLParser


class HTMLStripper(HTMLParser):
    """Strips HTML tags and converts structure into speech-friendly text."""

    def __init__(self):
        super().__init__()
        self.result = []
        self._current_tag = None
        self._skip_tags = {"style", "script"}
        self._heading = False
        self._skip = False

    def handle_starttag(self, tag, attrs):
        self._current_tag = tag
        classes = dict(attrs).get("class", "")

        if tag in self._skip_tags:
            self._skip = True
            return

        if tag == "h1":
            self.result.append("\n\n")
            self._heading = True
        elif tag == "h2":
            self.result.append("\n\n...\n\n")
            self._heading = True

        if "chantblock" in classes:
            self.result.append("\n\n...\n\n")

        if "highlightbox" in classes:
            self.result.append("\n...\n")

    def handle_endtag(self, tag):
        if tag in self._skip_tags:
            self._skip = False
            return

        if tag == "p":
            self.result.append("\n\n")
        elif tag in ("h1", "h2"):
            self._heading = False

        self._current_tag = None

    def handle_data(self, data):
        if self._skip or self._heading:
            return
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

    # Remove signature and archive footer
    text = re.sub(r"Nes Shine\s*SESSION ID.*$", "", text, flags=re.DOTALL)

    # Clean up excessive whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)

    return text.strip()


def prepare_for_speech(clean_text):
    """Final pass: clean up for natural speech delivery."""
    lines = clean_text.split("\n\n")
    processed = [line.strip() for line in lines if line.strip()]
    return "\n\n".join(processed)


def chunk_text(text, max_chars=4500):
    """
    Splits text into chunks of max_chars at paragraph boundaries.
    Uses 4500 instead of 5000 to leave safety margin.
    Never splits mid-sentence.
    """
    paragraphs = text.split("\n\n")
    chunks = []
    current_chunk = ""

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        # If adding this paragraph exceeds the limit, save current chunk and start new
        if current_chunk and (len(current_chunk) + len(para) + 2) > max_chars:
            chunks.append(current_chunk.strip())
            current_chunk = para
        else:
            if current_chunk:
                current_chunk += "\n\n" + para
            else:
                current_chunk = para

    # Don't forget the last chunk
    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks


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

        self.model = "eleven_v3"

    def generate_audio(self, html_text, output_filename="reading.mp3", progress_callback=None):
        """
        Takes raw HTML reading text, strips it, chunks it (max 5000 chars per request),
        generates audio for each chunk, combines them, and tracks cost.

        Returns: (filepath, cost_info) on success, (None, None) on failure.
        """
        # Step 1: Strip HTML
        clean = strip_html(html_text)

        # Step 2: Prepare for speech
        speech_text = prepare_for_speech(clean)

        if not speech_text or len(speech_text) < 100:
            print("AUDIO WARNING: Text too short for audio generation.")
            return None, None

        # Step 3: Chunk the text (Eleven v3 has 5000 char limit)
        chunks = chunk_text(speech_text, max_chars=4500)
        total_chars = len(speech_text)
        print(f"AUDIO: {total_chars} characters split into {len(chunks)} chunks.")

        # Step 4: Generate audio for each chunk and track costs
        audio_parts = []
        total_char_cost = 0

        for i, chunk in enumerate(chunks):
            chunk_num = i + 1
            if progress_callback:
                progress_callback(f"Ses: Parça {chunk_num}/{len(chunks)} üretiliyor ({len(chunk)} karakter)...")

            try:
                response = self.client.text_to_speech.with_raw_response.convert(
                    text=chunk,
                    voice_id=self.voice_id,
                    model_id=self.model,
                )

                # Track character cost from headers
                char_count = response.headers.get("x-character-count", "0")
                total_char_cost += int(char_count)

                # Collect audio data
                audio_parts.append(response.parse())

                print(f"AUDIO: Chunk {chunk_num}/{len(chunks)} done. Characters billed: {char_count}")

            except Exception as e:
                print(f"AUDIO ERROR on chunk {chunk_num}: {e}")
                if progress_callback:
                    progress_callback(f"Ses hatası (parça {chunk_num}): {str(e)[:80]}")
                return None, None

        # Step 5: Combine all audio chunks into one file
        save_dir = "saved_audio"
        os.makedirs(save_dir, exist_ok=True)
        filepath = os.path.join(save_dir, output_filename)

        with open(filepath, "wb") as f:
            for part in audio_parts:
                if isinstance(part, bytes):
                    f.write(part)
                else:
                    # If it's a generator/iterator, consume it
                    for audio_bytes in part:
                        f.write(audio_bytes)

        cost_info = {
            "total_characters": total_chars,
            "characters_billed": total_char_cost,
            "chunks": len(chunks),
        }

        print(f"AUDIO: Saved to {filepath}. Total billed: {total_char_cost} chars across {len(chunks)} chunks.")
        return filepath, cost_info
