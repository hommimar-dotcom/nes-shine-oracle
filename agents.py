
import os
import time
import json
import google.generativeai as genai
from prompts import NES_SHINE_CORE_INSTRUCTIONS, GRANDMASTER_QC_PROMPT, CLIENT_ID_PROMPT, MEMORY_UPDATE_PROMPT

class OracleBrain:
    # SADECE Gemini 3 Pro - BAŞKA MODEL KULLANILMAZ
    PRIMARY_MODEL = "gemini-3.1-pro-preview"
    
    # Gemini 3.1 Pro Pricing (USD per million tokens, <200K context)
    PRICE_INPUT_PER_M = 2.00
    PRICE_OUTPUT_PER_M = 12.00
    
    def __init__(self, api_keys):
        self.api_keys = api_keys if isinstance(api_keys, list) else [api_keys]
        self.current_key_index = 0
        self.current_model_name = self.PRIMARY_MODEL
        self.FALLBACK_MODEL = "gemini-3-pro-preview"  # Fail-safe model
        self._reset_usage_stats()
        self._configure_genai()
    
    def _reset_usage_stats(self):
        """Reset token counters for a new reading cycle."""
        self.usage_stats = {
            "tokens_in": 0,
            "tokens_out": 0,
            "total_tokens": 0,
            "api_calls": 0,
            "cost_usd": 0.0,
            "qc_rounds": 0
        }
    
    def _track_usage(self, response):
        """Extract and accumulate token usage from a Gemini response."""
        try:
            meta = response.usage_metadata
            if meta:
                t_in = meta.prompt_token_count or 0
                t_out = meta.candidates_token_count or 0
                self.usage_stats["tokens_in"] += t_in
                self.usage_stats["tokens_out"] += t_out
                self.usage_stats["total_tokens"] += (t_in + t_out)
                self.usage_stats["api_calls"] += 1
                # Calculate cost
                cost = (t_in / 1_000_000 * self.PRICE_INPUT_PER_M) + (t_out / 1_000_000 * self.PRICE_OUTPUT_PER_M)
                self.usage_stats["cost_usd"] += cost
                print(f"USAGE: +{t_in} in / +{t_out} out = ${cost:.4f} (Running: ${self.usage_stats['cost_usd']:.4f})")
        except Exception as e:
            print(f"USAGE TRACKING ERROR: {e}")

    def _configure_genai(self):
        current_key = self.api_keys[self.current_key_index]
        genai.configure(api_key=current_key)
        print(f"DEBUG: Switched to API Key Index {self.current_key_index}")

        
        # Generation config - YÜKSEKtemperature = DAHA İNSANSI YAZI
        # temperature 1.3 = daha yaratıcı, daha az tahmin edilebilir
        # top_p 0.95 = geniş kelime havuzu
        # top_k 64 = daha fazla seçenek
        self.generation_config = genai.types.GenerationConfig(
            temperature=1.3,
            top_p=0.95,
            top_k=64
        )
        
        from google.generativeai.types import HarmCategory, HarmBlockThreshold
        
        # SAFETY SETTINGS: BLOCK_NONE (Crucial for Occult/Esoteric topics to not trigger false positives)
        self.safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }
        
        self.model = genai.GenerativeModel(
            self.current_model_name,
            generation_config=self.generation_config,
            safety_settings=self.safety_settings
        )
        
        # LOW TEMP CONFIG FOR FACTS (Extraction & System Messages)
        self.extraction_config = genai.types.GenerationConfig(
            temperature=0.1, # Low temp specifically to prevent hallucinations
            top_p=0.95,
            top_k=64,
        )
        self.extraction_model = genai.GenerativeModel(
            self.current_model_name,
            generation_config=self.extraction_config,
            safety_settings=self.safety_settings
        )
        
    def identify_client(self, text):
        """Extracts client name from order note."""
        prompt = CLIENT_ID_PROMPT.format(text=text)
        # Use Low Temp Model with Retry
        resp = self.generate_with_retry(self.extraction_model, prompt)
        identified_name = resp.text.strip()
        self.last_client_name = identified_name
        return identified_name


    def update_memory(self, reading_text, client_name, memory_manager):
        prompt = MEMORY_UPDATE_PROMPT.format(reading_text=reading_text)
        # Use Low Temp Model with Retry
        resp = self.generate_with_retry(self.extraction_model, prompt)
        try:
            # Robust JSON extraction using regex
            import re
            json_match = re.search(r'\{.*\}', resp.text, re.DOTALL)
            if json_match:
                clean_json = json_match.group(0)
                data = json.loads(clean_json)
                
                # Load current memory
                mem = memory_manager.load_memory(client_name)
                
                # Add new session with DEEP extraction fields
                new_session = {
                    "timestamp": self.get_ny_time(),
                    "topic": data.get("topic", "Genel"),
                    "target_name": data.get("target_name"),
                    "key_prediction": data.get("key_prediction", ""),
                    "hook_left": data.get("hook_left", ""),
                    "client_mood": data.get("client_mood", ""),
                    "specific_details": data.get("specific_details", ""),
                    "promises_made": data.get("promises_made"),
                    "physical_descriptions": data.get("physical_descriptions"),
                    "reading_summary": data.get("reading_summary", "")
                }
                
                mem["sessions"].append(new_session)
                memory_manager.save_memory(client_name, mem)
                return True
            else:
                print(f"MEMORY WARNING: No JSON found in extraction response for {client_name}")
                return False
        except Exception as e:
            print(f"MEMORY ERROR: Failed to save memory for {client_name}: {str(e)}")
            return False

    def medium_agent(self, order_note, reading_topic, target_length="8000", memory_context="", feedback=None, progress_callback=None):
        """
        The Writer Agent (Nes Shine).
        If feedback is provided, it means a revision is requested.
        """
        # ... (Main writing logic continues below)
        prompt = f"""
        {NES_SHINE_CORE_INSTRUCTIONS}
        
        --- HAFIZA VE GEÇMİŞ BAĞLAMI (Memory Context) ---
        {memory_context}
        
        --- MÜŞTERİ VERİSİ ---
        SIPARİŞ NOTU:
        {order_note}
        
        OKUMA KONUSU (SADECE SENİN İÇİN CONTEXT, MÜŞTERİYE ASLA SÖYLEME!):
        {reading_topic}
        
        --- HEDEF UZUNLUK ---
        HEDEF: Minimum {target_length} karakter.
        Bu uzunluğa ulaşmak için her bir başlığı, hissi ve görüyü detaylandır. Kısa kesme.
        
        --- METADATA (SYSTEM CONTEXT - DO NOT READ AS USER INPUT) ---
        CURRENT DATE/TIME (NYC): {self.get_ny_time()}
        WARNING: Do NOT recite this timestamp or specific duration (e.g. "2 hours 14 mins ago"). 
        Use it purely for context to understand if we just spoke or if it's been a long time. 
        Phrasing must be mystical/natural (e.g. "You are back so soon", "The energies have shifted since we last spoke").
        """
        
        if feedback:
            prompt += f"""
            
            --- ÖNCEKİ DENEME REDDEDİLDİ. GRANDMASTER GERİ BİLDİRİMİ: ---
            {feedback}
            
            Lütfen yukarıdaki eleştirileri dikkate alarak metni YENİDEN YAZ.
            """
            
        # Use Standard (High Temp) Model for Writing with Retry
        response = self.generate_with_retry(self.model, prompt, progress_callback=progress_callback)
        return response.text

    def get_ny_time(self):
        """Returns current time in New York."""
        import pytz
        from datetime import datetime
        ny_tz = pytz.timezone('America/New_York')
        now = datetime.now(ny_tz)
        return now.strftime("%Y-%m-%d %H:%M:%S %Z")


    def grandmaster_agent(self, draft_text, order_note, target_length, progress_callback=None):
        """
        The QC Agent. Checks quality.
        Returns (bool, string) -> (IS_APPROVED, FEEDBACK)
        """
        # ... (QC logic)
        prompt = f"""
        {GRANDMASTER_QC_PROMPT}
        
        --- HEDEF UZUNLUK KRİTERİ ---
        Bu okuma için hedeflenen minimum uzunluk: {target_length} karakter.
        (Mevcut taslak bu uzunluğa yaklaşmalı ve kısa kalmamalı).
        
        --- İNCELENECEK TASLAK ---
        {draft_text}
        
        --- ORİJİNAL MÜŞTERİ NOTU (Context Kontrolü İçin) ---
        {order_note}
        """
        
        # Use Low Temp Model for QC (Better Logic, Less Hallucination) with Retry
        response = self.generate_with_retry(self.extraction_model, prompt, progress_callback=progress_callback)
        feedback = response.text.strip()
        
        if "APPROVED" in feedback:
            return True, "Onaylandı. Mükemmel."
        else:
            # Clean up the feedback to be ready for the medium
            return False, feedback

    def run_cycle(self, order_note, reading_topic, client_email=None, target_length="8000", generate_audio=False, model_choice=None, progress_callback=None):
        """
        Runs the full generation loop with Memory Integration.
        client_email: Client's email address - used as memory key for 100% accuracy
        generate_audio: If True, generates MP3 via ElevenLabs after approval.
        model_choice: The specific Gemini model to use for this generation.
        Returns: (reading_text, delivery_msg, usage_stats, audio_path)
        """
        
        # 0. APPLY MODEL SELECTION IF PROVIDED
        if model_choice and model_choice != self.current_model_name:
            if progress_callback: progress_callback(f"Model Yapılandırılıyor: {model_choice}...")
            self.current_model_name = model_choice
            self._configure_genai()
            self._reinit_models()
            
        from memory import MemoryManager
        mem_mgr = MemoryManager()
        self._reset_usage_stats()
        
        # 2. DETERMINE MEMORY KEY (Use Email if provided, otherwise fallback to client name)
        # Note: If email provided, we load memory first to see if we already know the name
        
        real_client_name = None
        memory_data = {}
        
        if client_email:
            memory_key = client_email
            memory_data = mem_mgr.load_memory(memory_key)
            if memory_data and memory_data.get("client_name") and "Unknown" not in memory_data["client_name"]:
                real_client_name = memory_data["client_name"]
        
        # 1. IDENTIFY CLIENT NAME (If not found in memory)
        if not real_client_name:
            if progress_callback: progress_callback("Nes Shine: Müşteri Kimliği Taranıyor...")
            extracted_name = self.identify_client(order_note)
            real_client_name = extracted_name
            # Update memory_data with the extracted name for consistency
            if memory_data:
                memory_data["client_name"] = real_client_name
        
        if progress_callback: progress_callback(f"Müşteri Tanımlandı: {real_client_name}")
        
        # Final Name Assignment
        client_name = real_client_name
        memory_key = client_email if client_email else client_name
        
        # 3. LOAD MEMORY (If not already loaded)
        if not memory_data:
            memory_data = mem_mgr.load_memory(memory_key)
            
        memory_context = mem_mgr.format_context_for_prompt(memory_data)
        
        if progress_callback: progress_callback("Akashic Records (Hafıza) Yüklendi...")
        
        # 4. DRAFTING LOOP
        if progress_callback: progress_callback("Nes Shine tünelliyor... (Taslak Hazırlanıyor)")
        
        draft = self.medium_agent(order_note, reading_topic, target_length, memory_context, progress_callback=progress_callback)
        
        # QC Loop - SINIRSIZ: %100 ONAY ALANA KADAR DEVAM EDER
        iteration = 0
        while True:
            iteration += 1
            if progress_callback: progress_callback(f"Grandmaster Kalite Kontrolü Yapıyor... (Tur {iteration})")
            
            approved, review_notes = self.grandmaster_agent(draft, order_note, target_length, progress_callback=progress_callback)
            
            if approved and iteration < 4:
                approved = False
                review_notes = "Metin teknik olarak onaylanabilir düzeyde, ancak yeterince ruh ve derinlik barındırmıyor. Mistik detayları, duyusal betimlemeleri ve Nes Shine'ın imzası olan otoriter, karanlık enerjiyi çok daha fazla hissettirerek metni GENİŞLET ve BAŞTAN YAZ. Bu bir asgari kalite testidir, henüz mükemmel değil."
                if progress_callback: progress_callback(f"Asgari Kalite Zorunluluğu (Tur {iteration}/4). Metin Derinleştiriliyor...")

            if approved:
                self.usage_stats["qc_rounds"] = iteration
                if progress_callback: progress_callback(f"Grandmaster Onayladı! ({iteration}. turda mükemmelliğe ulaşıldı)")
                if progress_callback: progress_callback("Nes Shine Hafızaya Kaydediyor...")
                self.update_memory(draft, memory_key, mem_mgr)
                
                # SAVE USAGE DATA
                try:
                    mem_mgr.save_usage(client_email or client_name, reading_topic, self.usage_stats)
                except Exception as e:
                    print(f"USAGE SAVE ERROR: {e}")
                
                # AUDIO GENERATION (only if requested)
                audio_path = None
                audio_cost = None
                if generate_audio:
                    if progress_callback: progress_callback("Ses üretiliyor (ElevenLabs)...")
                    try:
                        from audio_service import AudioService
                        audio_svc = AudioService()
                        audio_filename = f"{client_name.replace(' ', '_').lower()}_{int(time.time())}.mp3"
                        audio_path, audio_cost = audio_svc.generate_audio(
                            draft,
                            output_filename=audio_filename,
                            progress_callback=progress_callback
                        )
                        if progress_callback and audio_path:
                            chars = audio_cost.get('characters_billed', 0) if audio_cost else 0
                            chunks = audio_cost.get('chunks', 0) if audio_cost else 0
                            progress_callback(f"Ses hazır. {chars} karakter, {chunks} parça.")
                    except Exception as e:
                        print(f"AUDIO ERROR: {e}")
                        import traceback
                        traceback.print_exc()
                        if progress_callback: progress_callback(f"AUDIO HATASI: {str(e)[:200]}")
                
                # DELIVERY MESSAGE
                if progress_callback: progress_callback("Teslim mesajı hazırlanıyor...")
                delivery_msg = self.generate_delivery_message(client_name, reading_topic)
                
                return draft, delivery_msg, self.usage_stats, audio_path
            
            draft = self.medium_agent(order_note, reading_topic, target_length, memory_context, feedback=review_notes, progress_callback=progress_callback)
    
    def generate_delivery_message(self, client_name, reading_topic):
        """Generates a short delivery message for the client."""
        from prompts import DELIVERY_MESSAGE_PROMPT
        try:
            prompt = DELIVERY_MESSAGE_PROMPT.format(
                client_name=client_name,
                reading_topic=reading_topic
            )
            # Use Main Creative Model with Retry
            response = self.generate_with_retry(self.model, prompt)
            return response.text.strip()
        except Exception as e:
            return f"Hi {client_name}, your reading is ready. Take a quiet moment to receive it. — Nes"
    def generate_with_retry(self, model, prompt, progress_callback=None):
        """Wrapper for generate_content with API Key Rotation & Infinite Retry"""
        from google.api_core import exceptions
        import time
        
        attempt = 0
        blocked_retries = 0
        consecutive_exhaustions = 0
        max_blocked_retries = 5
        while True:
            attempt += 1
            try:
                target_model = self.model if getattr(model, 'model_name', None) == self.model.model_name else self.extraction_model
                
                # UZUN ZAMAN AŞIMI: 3.1 Pro çok yavaş kalabiliyor, Google'ı 5 dakika bekliyoruz.
                response = target_model.generate_content(prompt, request_options={'timeout': 300})
                
                # CHECK FOR BLOCKED/EMPTY RESPONSE
                if not response.candidates:
                    blocked_retries += 1
                    block_reason = "UNKNOWN"
                    try:
                        block_reason = str(response.prompt_feedback)
                    except:
                        pass
                    
                    if blocked_retries >= max_blocked_retries:
                        # After max retries, try rotating API key
                        err_msg = f"İÇERİK BLOKU {blocked_retries}x TEKRARLANDI. Anahtar değiştiriliyor..."
                        print(err_msg)
                        if progress_callback: progress_callback(err_msg)
                        original_index = self.current_key_index
                        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
                        if self.current_key_index != original_index and self.api_keys[self.current_key_index]:
                            self._configure_genai()
                            self._reinit_models()
                            blocked_retries = 0  # Reset counter for new key
                        else:
                            err_msg = f"TÜM ANAHTARLAR BLOKLU. 30s bekleniyor..."
                            print(err_msg)
                            if progress_callback: progress_callback(err_msg)
                            time.sleep(30)
                            blocked_retries = 0
                        continue
                    
                    err_msg = f"İÇERİK BLOKU (Tur {blocked_retries}/{max_blocked_retries}): {block_reason[:80]}. 5s sonra tekrar deniyor..."
                    print(err_msg)
                    if progress_callback: progress_callback(err_msg)
                    time.sleep(5)
                    continue
                
                self._track_usage(response)
                consecutive_exhaustions = 0
                return response
            except (exceptions.DeadlineExceeded, exceptions.ServiceUnavailable, exceptions.InternalServerError, exceptions.RetryError) as e:
                if self.current_model_name != self.FALLBACK_MODEL:
                    # Switch to 3.0 Pro fallback if 3.1 Pro backend crashes / times out
                    err_msg_sleep = f"Google 3.1 PRO ÇÖKTÜ ({type(e).__name__}). 3.0 PRO Yedeğine Geçiliyor..."
                    print(err_msg_sleep)
                    if progress_callback: progress_callback(err_msg_sleep)
                    
                    self.current_model_name = self.FALLBACK_MODEL
                    self._configure_genai()
                    self._reinit_models()
                    continue
                else:
                    err_msg_sleep = f"API YOĞUN ({type(e).__name__}) - Tur {attempt}. 15s bekleniyor..."
                    print(err_msg_sleep)
                    if progress_callback: progress_callback(err_msg_sleep)
                    time.sleep(15)
                    continue
                    
            except exceptions.InvalidArgument as e:
                err_msg = f"KONTROL HATASI (Invalid Argument). 5s bekleyip tekrar deniyor... {str(e)[:100]}"
                print(err_msg)
                if progress_callback: progress_callback(err_msg)
                time.sleep(5)
            except exceptions.ResourceExhausted:
                consecutive_exhaustions += 1
                if consecutive_exhaustions >= len(self.api_keys):
                    err_msg_sleep = "TÜM ANAHTARLAR TÜKENDİ. 60s bekleniyor..."
                    print(err_msg_sleep)
                    if progress_callback: progress_callback(err_msg_sleep)
                    time.sleep(60)
                    consecutive_exhaustions = 0
                    continue
                
                err_msg = f"API Limiti (429). Yedek Anahtara Geçiliyor... ({consecutive_exhaustions}/{len(self.api_keys)})"
                print(err_msg)
                if progress_callback: progress_callback(err_msg)
                
                while True:
                    self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
                    if self.api_keys[self.current_key_index]:
                        self._configure_genai()
                        self._reinit_models()
                        
                        msg_active = f"Anahtar {self.current_key_index + 1} ile üretim yapılıyor (Lütfen bekleyin)..."
                        print(msg_active)
                        if progress_callback: progress_callback(msg_active)
                        break
            except Exception as e:
                err_msg = f"BEKLENMEYEN HATA ({type(e).__name__}): {str(e)[:150]}... 10s bekleyip tekrar deniyor..."
                print(err_msg)
                if progress_callback: progress_callback(err_msg)
                time.sleep(10)
                    
    def stream_with_retry(self, model, prompt, progress_callback=None):
        """Streaming Generator Wrapper for generate_content with API Key Rotation & Infinite Retry"""
        from google.api_core import exceptions
        import time
        
        attempt = 0
        while True:
            attempt += 1
            try:
                target_model = self.model if getattr(model, 'model_name', None) == self.model.model_name else self.extraction_model
                response = target_model.generate_content(prompt, stream=True, request_options={'timeout': 300})
                full_text = ""
                for chunk in response:
                    full_text += chunk.text
                    yield chunk.text
                
                try:
                    if hasattr(response, 'usage_metadata'):
                        self._track_usage(response)
                except:
                    pass
                return
            except (exceptions.DeadlineExceeded, exceptions.ServiceUnavailable, exceptions.InternalServerError) as e:
                if self.current_model_name != self.FALLBACK_MODEL:
                    print(f"STREAM GOOGLE 3.1 ÇOKTÜ ({type(e).__name__}). 3.0 YEDEĞİNE GEÇİLİYOR...")
                    self.current_model_name = self.FALLBACK_MODEL
                    self._configure_genai()
                    self._reinit_models()
                    continue
                else:
                    print(f"STREAM WARNING: Transient stream error on attempt {attempt}. Retrying in 5s...")
                    time.sleep(5)
            except exceptions.InvalidArgument as e:
                print(f"CRITICAL STREAM ERROR: Invalid Argument: {str(e)}. Retrying...")
                time.sleep(5)
            except exceptions.ResourceExhausted:
                print("WARNING STREAM: API Key Exhausted (429). Attempting rotation...")
                original_index = self.current_key_index
                while True:
                    self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
                    if self.current_key_index == original_index:
                        print("ALL API KEYS EXHAUSTED DURING STREAM. Sleeping 60s before retrying...")
                        time.sleep(60)
                        break
                    if self.api_keys[self.current_key_index]:
                        self._configure_genai()
                        self._reinit_models()
                        break
            except Exception as e:
                err_msg = f"YAYIN GECİKMESİ/HATA ({type(e).__name__}): {str(e)[:150]}... 10s bekleyip tekrar deniyor..."
                print(err_msg)
                if progress_callback: progress_callback(err_msg)
                time.sleep(10)

    def _reinit_models(self):
        self.model = genai.GenerativeModel(
            self.current_model_name,
            generation_config=self.generation_config,
            safety_settings=self.safety_settings
        )
        self.extraction_model = genai.GenerativeModel(
            self.current_model_name,
            generation_config=self.extraction_config,
            safety_settings=self.safety_settings
        )
