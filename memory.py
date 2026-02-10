
import json
import os
import re
import datetime

def sanitize_filename(name):
    return re.sub(r'[^a-zA-Z0-9]', '', name)


def get_supabase_client():
    """Get Supabase client using environment variables or Streamlit secrets."""
    try:
        from supabase import create_client
        
        # Try environment variables first
        url = os.environ.get("SUPABASE_URL", "")
        key = os.environ.get("SUPABASE_KEY", "")
        
        # Try Streamlit secrets if env vars not set
        if not url or not key:
            try:
                import streamlit as st
                url = st.secrets.get("SUPABASE_URL", "")
                key = st.secrets.get("SUPABASE_KEY", "")
            except:
                pass
        
        if url and key:
            return create_client(url, key)
        return None
    except ImportError:
        return None


class MemoryManager:
    def __init__(self):
        self.supabase = get_supabase_client()
        self.use_db = self.supabase is not None
        
        # Fallback to local files if no Supabase
        if not self.use_db:
            if not os.path.exists("client_memories"):
                os.makedirs("client_memories")

    # ==================== LOAD ====================
    def load_memory(self, client_name):
        if self.use_db:
            return self._db_load(client_name)
        return self._file_load(client_name)
    
    def _db_load(self, client_name):
        key = sanitize_filename(client_name)
        try:
            result = self.supabase.table("client_memories").select("*").eq("client_key", key).execute()
            if result.data:
                row = result.data[0]
                return {
                    "client_name": row["client_name"],
                    "sessions": json.loads(row["sessions"])
                }
        except:
            pass
        return {"client_name": client_name, "sessions": []}
    
    def _file_load(self, client_name):
        filename = f"{sanitize_filename(client_name)}.json"
        path = os.path.join("client_memories", filename)
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {"client_name": client_name, "sessions": []}

    # ==================== SAVE ====================
    def save_memory(self, client_name, memory_data):
        if self.use_db:
            return self._db_save(client_name, memory_data)
        return self._file_save(client_name, memory_data)
    
    def _db_save(self, client_name, memory_data):
        key = sanitize_filename(client_name)
        row = {
            "client_key": key,
            "client_name": client_name,
            "sessions": json.dumps(memory_data.get("sessions", []), ensure_ascii=False),
            "updated_at": datetime.datetime.now().isoformat()
        }
        try:
            # Upsert (insert or update)
            self.supabase.table("client_memories").upsert(row, on_conflict="client_key").execute()
            return True
        except Exception as e:
            print(f"DB save error: {e}")
            return False
    
    def _file_save(self, client_name, memory_data):
        filename = f"{sanitize_filename(client_name)}.json"
        path = os.path.join("client_memories", filename)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(memory_data, f, ensure_ascii=False, indent=4)

    # ==================== FORMAT ====================
    def format_context_for_prompt(self, memory_data):
        if not memory_data.get("sessions"):
            return "BU MÜŞTERİ İLE İLK DEFA GÖRÜŞÜYORSUN."
            
        context = f"BU MÜŞTERİ ({memory_data['client_name']}) İLE GEÇMİŞ GÖRÜŞMELERİN:\n"
        recent_history = memory_data["sessions"][-3:]
        
        for idx, session in enumerate(recent_history):
            context += f"\n--- SEANS {idx+1} ({session.get('date', 'Tarih Yok')}) ---\n"
            context += f"Konu: {session.get('topic', 'Belirtilmedi')}\n"
            context += f"Odaklanılan Kişi (Target): {session.get('target_name', 'Yok')}\n"
            context += f"Verilen Temel Tavsiye/Kehanet: {session.get('key_prediction', '')}\n"
            context += f"Bırakılan Hook (Kanca): {session.get('hook_left', '')}\n"
            context += f"Müşterinin Ruh Hali: {session.get('client_mood', '')}\n"
            
        context += "\n!!! KRİTİK: YUKARIDAKİ GEÇMİŞ BİLGİLERLE ASLA ÇELİŞME. DEVAMLILIK SAĞLA !!!\n"
        return context

    # ==================== LIST ALL ====================
    def list_all_clients(self):
        if self.use_db:
            return self._db_list_all()
        return self._file_list_all()
    
    def _db_list_all(self):
        clients = []
        try:
            result = self.supabase.table("client_memories").select("client_key, client_name, sessions").execute()
            for row in result.data:
                sessions = json.loads(row["sessions"]) if isinstance(row["sessions"], str) else row["sessions"]
                clients.append({
                    "filename": row["client_key"],
                    "client_name": row["client_name"],
                    "session_count": len(sessions) if sessions else 0
                })
        except:
            pass
        return clients
    
    def _file_list_all(self):
        clients = []
        if os.path.exists("client_memories"):
            for filename in os.listdir("client_memories"):
                if filename.endswith('.json'):
                    path = os.path.join("client_memories", filename)
                    try:
                        with open(path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            clients.append({
                                "filename": filename,
                                "client_name": data.get("client_name", filename.replace('.json', '')),
                                "session_count": len(data.get("sessions", []))
                            })
                    except:
                        clients.append({
                            "filename": filename,
                            "client_name": filename.replace('.json', ''),
                            "session_count": 0
                        })
        return clients

    # ==================== DELETE ====================
    def delete_client(self, client_name):
        if self.use_db:
            return self._db_delete(client_name)
        return self._file_delete(client_name)
    
    def _db_delete(self, client_name):
        key = sanitize_filename(client_name)
        try:
            self.supabase.table("client_memories").delete().eq("client_key", key).execute()
            return True
        except:
            return False
    
    def _file_delete(self, client_name):
        filename = f"{sanitize_filename(client_name)}.json"
        path = os.path.join("client_memories", filename)
        if os.path.exists(path):
            os.remove(path)
            return True
        return False

    # ==================== CREATE ====================
    def create_client(self, client_name, topic, key_prediction, hook_left, client_mood, target_name=None, date=None):
        if date is None:
            date = datetime.datetime.now().strftime("%Y-%m-%d")
        
        memory_data = self.load_memory(client_name)
        
        new_session = {
            "date": date,
            "topic": topic,
            "target_name": target_name, # Added field
            "key_prediction": key_prediction,
            "hook_left": hook_left,
            "client_mood": client_mood
        }
        
        memory_data["sessions"].append(new_session)
        self.save_memory(client_name, memory_data)
        return True

    # ==================== PDF ANALYZE ====================
    def analyze_pdf_and_create_client(self, client_email, pdf_file, api_key):
        import io
        from PyPDF2 import PdfReader
        import google.generativeai as genai
        
        try:
            pdf_reader = PdfReader(io.BytesIO(pdf_file.read()))
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() or ""
        except Exception as e:
            return False, f"PDF okuma hatası: {str(e)}"
        
        if not text.strip():
            return False, "PDF'den metin çıkarılamadı."
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-3-pro-preview")
        
        analysis_prompt = f"""
        Aşağıdaki psişik okuma metnini ve dosya ismini analiz et. Şu bilgileri JSON formatında döndür:
        
        DOSYA İSMİ İPUCU: "{pdf_file.name}" (Müşteri ismi burada yazıyor olabilir)
        
        {{
            "topic": "Okumanın ana konusu (örn: Love & Relationship, Career)",
            "key_prediction": "Okumada verilen en önemli kehanet (1-2 cümle)",
            "hook_left": "Gelecek için bırakılan merak uyandırıcı ipucu (varsa)",
            "client_mood": "Müşterinin ruh hali",
            "client_name": "Müşterinin adı (Dosya isminden veya metindeki 'Dear X' hitabından çıkar)",
            "target_name": "Okumada adı geçen ve odaklanılan tüm kişiler (örn: Shane, Doug, Sarah). Aralarına virgül koyarak yaz. Yoksa null döndür."
        }}
        
        Sadece JSON döndür.
        
        OKUMA METNİ:
        """ + text[:12000] # Increased context window slightly
        
        try:
            response = model.generate_content(analysis_prompt)
            result_text = response.text.strip()
            
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0]
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0]
            
            # Parse JSON
            # import json # This import is already at the top of the file or implicitly available
            data = json.loads(result_text)
            
            extracted_name = data.get("client_name") or "Unknown_Client"
            # Fallback if name is still generic
            if "Unknown" in extracted_name:
                extracted_name = pdf_file.name.split('_')[0]
                
            # Create Memory
            self.create_client(
                client_name=extracted_name,
                topic=data.get("topic", "General Reading"),
                key_prediction=data.get("key_prediction", ""),
                hook_left=data.get("hook_left", ""),
                client_mood=data.get("client_mood", "Neutral"),
                target_name=data.get("target_name") # Pass target name
            )
            
            return True, "Başarılı"
            
        except Exception as e:
            return False, f"AI Analiz Hatası: {str(e)}"
