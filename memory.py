
import json
import os
import re

MEMORY_DIR = "client_memories"

def sanitize_filename(name):
    """
    Sanitizes string to be safe for filenames.
    """
    return re.sub(r'[^a-zA-Z0-9]', '', name)

class MemoryManager:
    def __init__(self):
        if not os.path.exists(MEMORY_DIR):
            os.makedirs(MEMORY_DIR)

    def load_memory(self, client_name):
        """
        Loads the memory file for a given client name.
        Returns a dictionary or empty structure if new.
        """
        filename = f"{sanitize_filename(client_name)}.json"
        path = os.path.join(MEMORY_DIR, filename)
        
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {"client_name": client_name, "sessions": []}
        else:
            return {"client_name": client_name, "sessions": []}

    def save_memory(self, client_name, memory_data):
        """
        Saves the updated memory data to JSON.
        """
        filename = f"{sanitize_filename(client_name)}.json"
        path = os.path.join(MEMORY_DIR, filename)
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(memory_data, f, ensure_ascii=False, indent=4)

    def format_context_for_prompt(self, memory_data):
        """
        Formats past sessions into a string string for the LLM prompt.
        Only takes the last 3 sessions to save context window (or all if short).
        """
        if not memory_data.get("sessions"):
            return "BU MÜŞTERİ İLE İLK DEFA GÖRÜŞÜYORSUN."
            
        context = f"BU MÜŞTERİ ({memory_data['client_name']}) İLE GEÇMİŞ GÖRÜŞMELERİN:\n"
        
        # Take last 3 sessions
        recent_history = memory_data["sessions"][-3:]
        
        for idx, session in enumerate(recent_history):
            context += f"\n--- SEANS {idx+1} ({session.get('date', 'Tarih Yok')}) ---\n"
            context += f"Konu: {session.get('topic', 'Belirtilmedi')}\n"
            context += f"Verilen Temel Tavsiye/Kehanet: {session.get('key_prediction', '')}\n"
            context += f"Bırakılan Hook (Kanca): {session.get('hook_left', '')}\n"
            context += f"Müşterinin Ruh Hali: {session.get('client_mood', '')}\n"
            
        context += "\n!!! KRİTİK: YUKARIDAKİ GEÇMİŞ BİLGİLERLE ASLA ÇELİŞME. DEVAMLILIK SAĞLA !!!\n"
        return context

    def list_all_clients(self):
        """
        Returns a list of all clients in memory.
        """
        clients = []
        if os.path.exists(MEMORY_DIR):
            for filename in os.listdir(MEMORY_DIR):
                if filename.endswith('.json'):
                    path = os.path.join(MEMORY_DIR, filename)
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

    def delete_client(self, client_name):
        """
        Deletes a client's memory file.
        """
        filename = f"{sanitize_filename(client_name)}.json"
        path = os.path.join(MEMORY_DIR, filename)
        
        if os.path.exists(path):
            os.remove(path)
            return True
        return False

    def create_client(self, client_name, topic, key_prediction, hook_left, client_mood, date=None):
        """
        Manually creates a client with past session data.
        Used for importing old clients before the system existed.
        """
        import datetime
        
        if date is None:
            date = datetime.datetime.now().strftime("%Y-%m-%d")
        
        # Load existing or create new
        memory_data = self.load_memory(client_name)
        
        # Add new session
        new_session = {
            "date": date,
            "topic": topic,
            "key_prediction": key_prediction,
            "hook_left": hook_left,
            "client_mood": client_mood
        }
        
        memory_data["sessions"].append(new_session)
        self.save_memory(client_name, memory_data)
        
        return True

    def analyze_pdf_and_create_client(self, client_email, pdf_file, api_key):
        """
        Analyzes a PDF reading file using AI and automatically extracts all session data.
        """
        import io
        from PyPDF2 import PdfReader
        import google.generativeai as genai
        
        # Extract text from PDF
        try:
            pdf_reader = PdfReader(io.BytesIO(pdf_file.read()))
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() or ""
        except Exception as e:
            return False, f"PDF okuma hatası: {str(e)}"
        
        if not text.strip():
            return False, "PDF'den metin çıkarılamadı."
        
        # Use AI to analyze the reading
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-3-pro-preview")
        
        analysis_prompt = """
        Aşağıdaki psişik okuma metnini analiz et ve şu bilgileri JSON formatında döndür:
        
        {
            "topic": "Okumanın ana konusu (örn: Love & Relationship, Career, Spiritual Growth)",
            "key_prediction": "Okumada verilen en önemli kehanet veya tavsiye (1-2 cümle)",
            "hook_left": "Gelecek için bırakılan merak uyandırıcı ipucu/kanca (varsa)",
            "client_mood": "Müşterinin ruh hali (Hopeful, Anxious, Sad, Confused, Excited, Neutral)",
            "client_name": "Metinde geçen müşteri adı (varsa)"
        }
        
        Sadece JSON döndür, başka bir şey yazma.
        
        OKUMA METNİ:
        """ + text[:8000]  # Limit text to avoid token overflow
        
        try:
            response = model.generate_content(analysis_prompt)
            result_text = response.text.strip()
            
            # Clean up JSON
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0]
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0]
            
            import json
            analysis = json.loads(result_text)
            
            # Create client with analyzed data
            import datetime
            self.create_client(
                client_name=client_email,
                topic=analysis.get("topic", "Unknown"),
                key_prediction=analysis.get("key_prediction", ""),
                hook_left=analysis.get("hook_left", ""),
                client_mood=analysis.get("client_mood", "Neutral"),
                date=datetime.datetime.now().strftime("%Y-%m-%d")
            )
            
            return True, analysis
            
        except Exception as e:
            return False, f"AI analiz hatası: {str(e)}"
