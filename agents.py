
import os
import time
import json
import google.generativeai as genai
from prompts import NES_SHINE_CORE_INSTRUCTIONS, GRANDMASTER_QC_PROMPT, CLIENT_ID_PROMPT, MEMORY_UPDATE_PROMPT

class OracleBrain:
    # SADECE Gemini 3 Pro - BAŞKA MODEL KULLANILMAZ
    REQUIRED_MODEL = "gemini-3-pro-preview"
    
    def __init__(self, api_key):
        genai.configure(api_key=api_key)
        
        # Generation config - YÜKSEKtemperature = DAHA İNSANSI YAZI
        # temperature 1.3 = daha yaratıcı, daha az tahmin edilebilir
        # top_p 0.95 = geniş kelime havuzu
        # top_k 64 = daha fazla seçenek
        self.generation_config = genai.types.GenerationConfig(
            temperature=1.3,
            top_p=0.95,
            top_k=64,
            max_output_tokens=8192,
        )
        
        # SAFETY SETTINGS: BLOCK_NONE (Crucial for Occult/Esoteric topics to not trigger false positives)
        self.safety_settings = [
            { "category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE" },
            { "category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE" },
            { "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE" },
            { "category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE" },
        ]
        
        self.model = genai.GenerativeModel(
            self.REQUIRED_MODEL,
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
            self.REQUIRED_MODEL,
            generation_config=self.extraction_config,
            safety_settings=self.safety_settings
        )
        
    def identify_client(self, text):
        """Extracts client name from order note."""
        prompt = CLIENT_ID_PROMPT.format(text=text)
        # Use Low Temp Model
        resp = self.extraction_model.generate_content(prompt)
        identified_name = resp.text.strip()
        self.last_client_name = identified_name
        return identified_name


    def update_memory(self, reading_text, client_name, memory_manager):
        prompt = MEMORY_UPDATE_PROMPT.format(reading_text=reading_text)
        # Use Low Temp Model
        resp = self.extraction_model.generate_content(prompt)
        try:
            # Robust JSON extraction using regex
            import re
            json_match = re.search(r'\{.*\}', resp.text, re.DOTALL)
            if json_match:
                clean_json = json_match.group(0)
                data = json.loads(clean_json)
                
                # Load current memory
                mem = memory_manager.load_memory(client_name)
                
                # Add new session — INCLUDING FULL READING TEXT
                new_session = {
                    "timestamp": self.get_ny_time(), # Full timestamp for precision
                    "topic": data.get("topic", "Genel"),
                    "target_name": data.get("target_name"),
                    "key_prediction": data.get("key_prediction", ""),
                    "hook_left": data.get("hook_left", ""),
                    "client_mood": data.get("client_mood", ""),
                    "full_reading": reading_text  # ← FULL READING TEXT SAVED
                }
                
                mem["sessions"].append(new_session)
                memory_manager.save_memory(client_name, mem)
                return True
            return False
        except:
            return False

    def medium_agent(self, order_note, reading_topic, target_length="8000", memory_context="", feedback=None):
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
        
        OKUMA KONUSU:
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
            
        # Use Standard (High Temp) Model for Writing
        response = self.model.generate_content(prompt, request_options={'timeout': 1200})
        return response.text

    def get_ny_time(self):
        """Returns current time in New York."""
        import pytz
        from datetime import datetime
        ny_tz = pytz.timezone('America/New_York')
        now = datetime.now(ny_tz)
        return now.strftime("%Y-%m-%d %H:%M:%S %Z")


    def grandmaster_agent(self, draft_text, order_note, target_length):
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
        
        # Use Low Temp Model for QC (Better Logic, Less Hallucination)
        response = self.extraction_model.generate_content(prompt, request_options={'timeout': 1200})
        feedback = response.text.strip()
        
        if "APPROVED" in feedback:
            return True, "Onaylandı. Mükemmel."
        else:
            # Clean up the feedback to be ready for the medium
            return False, feedback

    def run_cycle(self, order_note, reading_topic, client_email=None, target_length="8000", progress_callback=None):
        """
        Runs the full generation loop with Memory Integration.
        client_email: Client's email address (e.g., "jessica@gmail.com") - used as memory key for 100% accuracy
        """
        from memory import MemoryManager
        mem_mgr = MemoryManager()
        
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
        
        draft = self.medium_agent(order_note, reading_topic, target_length, memory_context)
        
        # QC Loop - SINIRSIZ: %100 ONAY ALANA KADAR DEVAM EDER
        iteration = 0
        while True:
            iteration += 1
            if progress_callback: progress_callback(f"Grandmaster Kalite Kontrolü Yapıyor... (Tur {iteration})")
            
            approved, review_notes = self.grandmaster_agent(draft, order_note, target_length)
            
            if approved:
                if progress_callback: progress_callback(f"Grandmaster Onayladı! ({iteration}. turda mükemmelliğe ulaşıldı)")
                if progress_callback: progress_callback("Nes Shine Hafızaya Kaydediyor...")
                self.update_memory(draft, memory_key, mem_mgr)
                
                # DELIVERY MESSAGE
                if progress_callback: progress_callback("Teslim mesajı hazırlanıyor...")
                delivery_msg = self.generate_delivery_message(client_name, reading_topic)
                
                return draft, delivery_msg
            
            if progress_callback: progress_callback(f"Revize gerekiyor (Tur {iteration}): {review_notes[:100]}...")
            draft = self.medium_agent(order_note, reading_topic, target_length, memory_context, feedback=review_notes)
    
    def generate_delivery_message(self, client_name, reading_topic):
        """Generates a short delivery message for the client."""
        from prompts import DELIVERY_MESSAGE_PROMPT
        try:
            prompt = DELIVERY_MESSAGE_PROMPT.format(
                client_name=client_name,
                reading_topic=reading_topic
            )
            # Use Low Temp Model
            response = self.extraction_model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            return f"Hi {client_name}, your reading is ready. Take a quiet moment to receive it. — Nes"
