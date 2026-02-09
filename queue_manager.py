
import json
import os
import time
from datetime import datetime

def get_supabase_client():
    """Get Supabase client using environment variables or Streamlit secrets."""
    try:
        from supabase import create_client
        
        # Try environment variables first
        url = os.environ.get("SUPABASE_URL", "")
        key = os.environ.get("SUPABASE_KEY", "")
        
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

class QueueManager:
    def __init__(self):
        self.supabase = get_supabase_client()
        self.use_db = self.supabase is not None
        self.queue_file = "reading_queue.json"
        
        if not self.use_db:
            self._ensure_queue_file()
    
    def _ensure_queue_file(self):
        """Creates queue file if it doesn't exist."""
        if not os.path.exists(self.queue_file):
            with open(self.queue_file, 'w') as f:
                json.dump({"queue": [], "completed": []}, f)
    
    def add_to_queue(self, client_email, order_note, reading_topic, target_length="8000"):
        """Adds a new reading request to the queue."""
        new_item = {
            "id": datetime.now().strftime("%Y%m%d%H%M%S"),
            "client_email": client_email,
            "order_note": order_note,
            "reading_topic": reading_topic,
            "target_length": target_length,
            "status": "pending",
            "added_at": datetime.now().isoformat(),
            "completed_at": None,
            "pdf_path": None
        }
        
        if self.use_db:
            try:
                self.supabase.table("reading_queue").insert(new_item).execute()
                return new_item["id"]
            except Exception as e:
                print(f"DB Error: {e}")
                # Fallback to file? keeping it simple for now
                return None
        
        # LOCAL FILE FALLBACK
        with open(self.queue_file, 'r') as f:
            data = json.load(f)
        
        data["queue"].append(new_item)
        
        with open(self.queue_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        return new_item["id"]
    
    def get_queue(self):
        """Returns all pending items in queue."""
        if self.use_db:
            try:
                response = self.supabase.table("reading_queue").select("*").eq("status", "pending").order("added_at").execute()
                return response.data
            except:
                return []
                
        with open(self.queue_file, 'r') as f:
            data = json.load(f)
        return [item for item in data["queue"] if item["status"] == "pending"]
    
    def get_completed(self, limit=10):
        """Returns last N completed items."""
        if self.use_db:
            try:
                # Note: Supabase ordering descending for latest
                response = self.supabase.table("reading_queue").select("*").in_("status", ["completed", "failed"]).order("completed_at", desc=True).limit(limit).execute()
                return response.data
            except:
                return []

        with open(self.queue_file, 'r') as f:
            data = json.load(f)
        return data["completed"][-limit:]
    
    def mark_processing(self, item_id):
        """Marks an item as currently processing."""
        if self.use_db:
            try:
                self.supabase.table("reading_queue").update({"status": "processing"}).eq("id", item_id).execute()
                return
            except:
                pass
                
        with open(self.queue_file, 'r') as f:
            data = json.load(f)
        
        for item in data["queue"]:
            if item["id"] == item_id:
                item["status"] = "processing"
                break
        
        with open(self.queue_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def mark_completed(self, item_id, pdf_path, delivery_msg=None):
        """Moves item from queue to completed."""
        completed_at = datetime.now().isoformat()
        
        if self.use_db:
            try:
                update_data = {
                    "status": "completed",
                    "completed_at": completed_at,
                    "pdf_path": pdf_path
                }
                if delivery_msg:
                    update_data["delivery_msg"] = delivery_msg
                    
                self.supabase.table("reading_queue").update(update_data).eq("id", item_id).execute()
                return
            except:
                pass

        with open(self.queue_file, 'r') as f:
            data = json.load(f)
        
        # Find and remove from queue
        completed_item = None
        for i, item in enumerate(data["queue"]):
            if item["id"] == item_id:
                completed_item = data["queue"].pop(i)
                completed_item["status"] = "completed"
                completed_item["completed_at"] = completed_at
                completed_item["pdf_path"] = pdf_path
                if delivery_msg:
                    completed_item["delivery_msg"] = delivery_msg
                break
        
        if completed_item:
            data["completed"].append(completed_item)
        
        with open(self.queue_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def mark_failed(self, item_id, error_message):
        """Marks an item as failed."""
        if self.use_db:
            try:
                self.supabase.table("reading_queue").update({
                    "status": "failed",
                    "error": error_message
                }).eq("id", item_id).execute()
                return
            except:
                pass
        
        with open(self.queue_file, 'r') as f:
            data = json.load(f)
        
        for item in data["queue"]:
            if item["id"] == item_id:
                item["status"] = "failed"
                item["error"] = error_message
                break
        
        with open(self.queue_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def get_stats(self):
        """Returns queue statistics."""
        if self.use_db:
            try:
                # A bit inefficient but works for small scale
                pending = self.supabase.table("reading_queue").select("id", count="exact").eq("status", "pending").execute().count
                processing = self.supabase.table("reading_queue").select("id", count="exact").eq("status", "processing").execute().count
                completed = self.supabase.table("reading_queue").select("id", count="exact").in_("status", ["completed", "failed"]).execute().count
                failed = self.supabase.table("reading_queue").select("id", count="exact").eq("status", "failed").execute().count
                
                return {
                    "pending": pending,
                    "processing": processing,
                    "completed": completed,
                    "failed": failed
                }
            except:
                return {"pending": 0, "processing": 0, "completed": 0, "failed": 0}

        with open(self.queue_file, 'r') as f:
            data = json.load(f)
        
        pending = len([item for item in data["queue"] if item["status"] == "pending"])
        processing = len([item for item in data["queue"] if item["status"] == "processing"])
        completed = len(data["completed"])
        failed = len([item for item in data["queue"] if item["status"] == "failed"])
        
        return {
            "pending": pending,
            "processing": processing,
            "completed": completed,
            "failed": failed
        }
