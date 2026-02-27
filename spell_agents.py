
import os
import time
import json
import re
import google.generativeai as genai
from spell_prompts import (
    SPELL_PERSONA, SPELL_KNOWLEDGE_BASE, FORTY_PILLARS,
    INCOMPATIBILITY_MATRIX, PLANETARY_TIMING, ANCIENT_LANGUAGE_LIBRARY,
    SPELL_DIAGNOSTIC_PROMPT, SPELL_RECOMMENDATION_PROMPT,
    SPELL_ARCHITECT_PROMPT, SPELL_QC_PROMPT,
    SPELL_MEMORY_UPDATE_PROMPT, SPELL_DELIVERY_PROMPT
)


class SpellBrain:
    """
    Nes Shine Spell Engine — The Sorcery Brain.
    Mirrors OracleBrain architecture but focused on spell/ritual operations.
    Uses the SAME API key rotation and retry logic.
    """
    
    PRIMARY_MODEL = "gemini-3.1-pro-preview"
    FALLBACK_MODEL = "gemini-3-pro-preview"
    PRICE_INPUT_PER_M = 2.00
    PRICE_OUTPUT_PER_M = 12.00
    
    def __init__(self, api_keys):
        self.api_keys = api_keys if isinstance(api_keys, list) else [api_keys]
        self.current_key_index = 0
        self.current_model_name = self.PRIMARY_MODEL
        self._reset_usage_stats()
        self._configure_genai()
    
    def _reset_usage_stats(self):
        self.usage_stats = {
            "tokens_in": 0,
            "tokens_out": 0,
            "total_tokens": 0,
            "api_calls": 0,
            "cost_usd": 0.0,
            "qc_rounds": 0
        }
    
    def _track_usage(self, response):
        try:
            meta = response.usage_metadata
            if meta:
                t_in = meta.prompt_token_count or 0
                t_out = meta.candidates_token_count or 0
                self.usage_stats["tokens_in"] += t_in
                self.usage_stats["tokens_out"] += t_out
                self.usage_stats["total_tokens"] += (t_in + t_out)
                self.usage_stats["api_calls"] += 1
                cost = (t_in / 1_000_000 * self.PRICE_INPUT_PER_M) + (t_out / 1_000_000 * self.PRICE_OUTPUT_PER_M)
                self.usage_stats["cost_usd"] += cost
                print(f"SPELL USAGE: +{t_in} in / +{t_out} out = ${cost:.4f} (Running: ${self.usage_stats['cost_usd']:.4f})")
        except Exception as e:
            print(f"SPELL USAGE TRACKING ERROR: {e}")

    def _configure_genai(self):
        current_key = self.api_keys[self.current_key_index]
        genai.configure(api_key=current_key)
        print(f"SPELL DEBUG: Switched to API Key Index {self.current_key_index}")
        
        # High creativity for ritual writing
        self.generation_config = genai.types.GenerationConfig(
            temperature=1.3,
            top_p=0.95,
            top_k=64
        )
        
        from google.generativeai.types import HarmCategory, HarmBlockThreshold
        
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
        
        # Low temp for diagnostics, extraction, QC
        self.extraction_config = genai.types.GenerationConfig(
            temperature=0.3,
            top_p=0.95,
            top_k=64,
        )
        self.extraction_model = genai.GenerativeModel(
            self.current_model_name,
            generation_config=self.extraction_config,
            safety_settings=self.safety_settings
        )

    # ==================== AGENT 1: SPIRITUAL DIAGNOSTIC ====================
    def spiritual_diagnostic(self, client_note, requested_work, memory_context="", progress_callback=None):
        """
        Performs a spiritual scan of the client's situation before recommending spells.
        Returns a diagnostic report string.
        """
        prompt = SPELL_DIAGNOSTIC_PROMPT.format(
            persona=SPELL_PERSONA,
            memory_context=memory_context,
            client_note=client_note,
            requested_work=requested_work,
            current_time=self.get_ny_time()
        )
        
        if progress_callback:
            progress_callback("Spiritual Diagnostic Scan in progress...")
        
        response = self.generate_with_retry(self.extraction_model, prompt, progress_callback=progress_callback)
        return response.text

    # ==================== AGENT 2: SPELL RECOMMENDER ====================
    def recommend_spells(self, diagnostic_report, red_alert_enabled=False, progress_callback=None):
        """
        Based on diagnostic, recommends 2-3 spell techniques as a cocktail.
        Returns recommendation text for operator review.
        """
        prompt = SPELL_RECOMMENDATION_PROMPT.format(
            persona=SPELL_PERSONA,
            knowledge_base=SPELL_KNOWLEDGE_BASE,
            incompatibility_matrix=INCOMPATIBILITY_MATRIX,
            planetary_timing=PLANETARY_TIMING,
            diagnostic_report=diagnostic_report,
            red_alert_status="YES — All spells including destructive operations are available" if red_alert_enabled else "NO — Only constructive, binding, and protective spells available. Destructive operations are LOCKED."
        )
        
        if progress_callback:
            progress_callback("Analyzing optimal spell cocktail...")
        
        response = self.generate_with_retry(self.extraction_model, prompt, progress_callback=progress_callback)
        return response.text

    # ==================== AGENT 3: SPELL ARCHITECT ====================
    def spell_architect(self, client_note, requested_work, approved_spells, diagnostic_report,
                        target_length="15000", memory_context="", feedback=None, progress_callback=None):
        """
        Writes the full ritual document. If feedback is provided, it's a revision.
        Returns the ritual HTML body text.
        """
        prompt = SPELL_ARCHITECT_PROMPT.format(
            persona=SPELL_PERSONA,
            approved_spells=approved_spells,
            diagnostic_report=diagnostic_report,
            knowledge_base=SPELL_KNOWLEDGE_BASE,
            ancient_languages=ANCIENT_LANGUAGE_LIBRARY,
            forty_pillars=FORTY_PILLARS,
            memory_context=memory_context,
            client_note=client_note,
            requested_work=requested_work,
            target_length=target_length,
            current_time=self.get_ny_time()
        )
        
        if feedback:
            prompt += f"""
            
            --- PREVIOUS DRAFT REJECTED. GRANDMASTER QC FEEDBACK: ---
            {feedback}
            
            Revise the text according to the above critique. Fix every issue.
            """
        
        if progress_callback:
            progress_callback("Spell Architect channeling ritual text...")
        
        response = self.generate_with_retry(self.model, prompt, progress_callback=progress_callback)
        return response.text

    # ==================== AGENT 4: GRANDMASTER SPELL QC ====================
    def grandmaster_spell_qc(self, ritual_text, client_note, requested_work, progress_callback=None):
        """
        15-point quality control. Returns (bool, string) -> (IS_APPROVED, FEEDBACK)
        """
        prompt = SPELL_QC_PROMPT.format(
            ritual_text=ritual_text,
            client_note=client_note,
            requested_work=requested_work
        )
        
        if progress_callback:
            progress_callback("Grandmaster QC evaluating ritual text (15 criteria)...")
        
        response = self.generate_with_retry(self.extraction_model, prompt, progress_callback=progress_callback)
        feedback = response.text.strip()
        
        if "APPROVED" in feedback:
            return True, "Approved. Flawless."
        else:
            return False, feedback

    # ==================== IDENTIFY CLIENT ====================
    def identify_client(self, text):
        from prompts import CLIENT_ID_PROMPT
        prompt = CLIENT_ID_PROMPT.format(text=text)
        resp = self.generate_with_retry(self.extraction_model, prompt)
        identified_name = resp.text.strip()
        self.last_client_name = identified_name
        return identified_name

    # ==================== UPDATE MEMORY ====================
    def update_spell_memory(self, ritual_text, memory_key, memory_manager):
        prompt = SPELL_MEMORY_UPDATE_PROMPT.format(ritual_text=ritual_text)
        resp = self.generate_with_retry(self.extraction_model, prompt)
        try:
            json_match = re.search(r'\{.*\}', resp.text, re.DOTALL)
            if json_match:
                clean_json = json_match.group(0)
                data = json.loads(clean_json)
                
                mem = memory_manager.load_memory(memory_key)
                
                new_session = {
                    "timestamp": self.get_ny_time(),
                    "session_type": "spell",
                    "topic": data.get("topic", "Spell Work"),
                    "target_name": data.get("target_name"),
                    "spells_used": data.get("spells_used", ""),
                    "client_tasks_given": data.get("client_tasks_given", ""),
                    "expected_timeline": data.get("expected_timeline", ""),
                    "warnings_given": data.get("warnings_given", ""),
                    "specific_details": data.get("specific_details", ""),
                    "follow_up_protocol": data.get("follow_up_protocol", ""),
                    "reading_summary": data.get("ritual_summary", "")
                }
                
                mem["sessions"].append(new_session)
                memory_manager.save_memory(memory_key, mem)
                return True
            else:
                print(f"SPELL MEMORY WARNING: No JSON found in extraction response")
                return False
        except Exception as e:
            print(f"SPELL MEMORY ERROR: {e}")
            return False

    # ==================== DELIVERY MESSAGE ====================
    def generate_delivery_message(self, client_name, work_type):
        try:
            prompt = SPELL_DELIVERY_PROMPT.format(
                client_name=client_name,
                work_type=work_type
            )
            response = self.generate_with_retry(self.model, prompt)
            return response.text.strip()
        except Exception as e:
            return f"The work is done. Take a quiet moment before you open this. Everything has been set in motion. — Nes"

    # ==================== FULL CYCLE ====================
    def run_spell_cycle(self, client_note, requested_work, client_email=None,
                        approved_spells="", diagnostic_report="",
                        target_length="15000", generate_audio=False,
                        progress_callback=None):
        """
        Runs the full spell generation loop AFTER operator has approved recommendations.
        Returns: (ritual_text, delivery_msg, usage_stats, audio_path)
        """
        from memory import MemoryManager
        mem_mgr = MemoryManager()
        self._reset_usage_stats()
        
        # 1. DETERMINE CLIENT
        real_client_name = None
        memory_data = {}
        
        if client_email:
            memory_key = client_email
            memory_data = mem_mgr.load_memory(memory_key)
            if memory_data and memory_data.get("client_name") and "Unknown" not in memory_data["client_name"]:
                real_client_name = memory_data["client_name"]
        
        if not real_client_name:
            if progress_callback:
                progress_callback("Identifying client...")
            extracted_name = self.identify_client(client_note)
            real_client_name = extracted_name
            if memory_data:
                memory_data["client_name"] = real_client_name
        
        if progress_callback:
            progress_callback(f"Client Identified: {real_client_name}")
        
        client_name = real_client_name
        memory_key = client_email if client_email else client_name
        
        if not memory_data:
            memory_data = mem_mgr.load_memory(memory_key)
        
        memory_context = mem_mgr.format_context_for_prompt(memory_data)
        
        if progress_callback:
            progress_callback("Memory loaded (Reading + Spell history)...")
        
        # 2. WRITE RITUAL
        if progress_callback:
            progress_callback("Spell Architect beginning ritual inscription...")
        
        draft = self.spell_architect(
            client_note, requested_work, approved_spells, diagnostic_report,
            target_length, memory_context, progress_callback=progress_callback
        )
        
        # 3. QC LOOP — INFINITE until 100% approval
        iteration = 0
        while True:
            iteration += 1
            if progress_callback:
                progress_callback(f"Grandmaster Spell QC — Round {iteration}...")
            
            approved, review_notes = self.grandmaster_spell_qc(
                draft, client_note, requested_work, progress_callback=progress_callback
            )
            
            if approved:
                self.usage_stats["qc_rounds"] = iteration
                if progress_callback:
                    progress_callback(f"Grandmaster Approved! (Round {iteration} — perfection achieved)")
                
                # Save to memory
                if progress_callback:
                    progress_callback("Saving spell record to memory...")
                self.update_spell_memory(draft, memory_key, mem_mgr)
                
                # Save usage
                try:
                    mem_mgr.save_usage(client_email or client_name, f"SPELL: {requested_work[:50]}", self.usage_stats)
                except Exception as e:
                    print(f"SPELL USAGE SAVE ERROR: {e}")
                
                # Audio generation
                audio_path = None
                if generate_audio:
                    if progress_callback:
                        progress_callback("Generating audio (ElevenLabs)...")
                    try:
                        from audio_service import AudioService
                        audio_svc = AudioService()
                        audio_filename = f"spell_{client_name.replace(' ', '_').lower()}_{int(time.time())}.mp3"
                        audio_path, audio_cost = audio_svc.generate_audio(
                            draft, output_filename=audio_filename, progress_callback=progress_callback
                        )
                        if progress_callback and audio_path:
                            chars = audio_cost.get('characters_billed', 0) if audio_cost else 0
                            progress_callback(f"Audio ready. {chars} characters processed.")
                    except Exception as e:
                        print(f"SPELL AUDIO ERROR: {e}")
                        import traceback
                        traceback.print_exc()
                        if progress_callback:
                            progress_callback(f"AUDIO ERROR: {str(e)[:200]}")
                
                # Delivery message
                if progress_callback:
                    progress_callback("Preparing delivery message...")
                delivery_msg = self.generate_delivery_message(client_name, requested_work)
                
                return draft, delivery_msg, self.usage_stats, audio_path
            
            # Revision needed
            if progress_callback:
                progress_callback(f"QC Round {iteration} — Revisions required. Spell Architect rewriting...")
            draft = self.spell_architect(
                client_note, requested_work, approved_spells, diagnostic_report,
                target_length, memory_context, feedback=review_notes,
                progress_callback=progress_callback
            )

    # ==================== UTILITY: NY TIME ====================
    def get_ny_time(self):
        import pytz
        from datetime import datetime
        ny_tz = pytz.timezone('America/New_York')
        now = datetime.now(ny_tz)
        return now.strftime("%Y-%m-%d %H:%M:%S %Z")

    # ==================== API RETRY LOGIC (mirrors OracleBrain) ====================
    def generate_with_retry(self, model, prompt, progress_callback=None):
        from google.api_core import exceptions
        
        attempt = 0
        consecutive_exhaustions = 0
        while True:
            attempt += 1
            try:
                target_model = self.model if getattr(model, 'model_name', None) == self.model.model_name else self.extraction_model
                response = target_model.generate_content(prompt, request_options={'timeout': 100000})
                self._track_usage(response)
                consecutive_exhaustions = 0
                return response
            except (exceptions.DeadlineExceeded, exceptions.ServiceUnavailable, exceptions.InternalServerError) as e:
                err_msg = f"SPELL API DELAY ({type(e).__name__}) — Round {attempt}. Retrying in 5s..."
                print(err_msg)
                if progress_callback:
                    progress_callback(err_msg)
                time.sleep(5)
            except exceptions.InvalidArgument as e:
                err_msg = f"SPELL VALIDATION ERROR (Invalid Argument). Retrying in 5s... {str(e)[:100]}"
                print(err_msg)
                if progress_callback:
                    progress_callback(err_msg)
                time.sleep(5)
            except exceptions.ResourceExhausted:
                consecutive_exhaustions += 1
                if consecutive_exhaustions >= len(self.api_keys):
                    if self.current_model_name == self.PRIMARY_MODEL:
                        err_msg_fallback = f"ALL KEYS EXHAUSTED FOR {self.PRIMARY_MODEL}. Falling back to {self.FALLBACK_MODEL}..."
                        print(err_msg_fallback)
                        if progress_callback:
                            progress_callback(err_msg_fallback)
                        
                        self.current_model_name = self.FALLBACK_MODEL
                        self._configure_genai()
                        self._reinit_models()
                        consecutive_exhaustions = 0
                        continue
                    else:
                        err_msg_sleep = "ALL KEYS AND MODELS EXHAUSTED. Waiting 60s..."
                        print(err_msg_sleep)
                        if progress_callback:
                            progress_callback(err_msg_sleep)
                        time.sleep(60)
                        consecutive_exhaustions = 0
                        
                        if self.current_model_name != self.PRIMARY_MODEL:
                            self.current_model_name = self.PRIMARY_MODEL
                            self._configure_genai()
                            self._reinit_models()
                        continue

                err_msg = f"API Limit (429). Rotating to backup key... ({consecutive_exhaustions}/{len(self.api_keys)})"
                print(err_msg)
                if progress_callback:
                    progress_callback(err_msg)
                
                while True:
                    self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
                    if self.api_keys[self.current_key_index]:
                        self._configure_genai()
                        self._reinit_models()
                        
                        msg_active = f"Key {self.current_key_index + 1} ACTIVE. Generating response (Stand by)..."
                        print(msg_active)
                        if progress_callback: progress_callback(msg_active)
                        break
            except Exception as e:
                err_msg = f"SPELL UNEXPECTED ERROR ({type(e).__name__}): {str(e)[:150]}... Retrying in 10s..."
                print(err_msg)
                if progress_callback:
                    progress_callback(err_msg)
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
