import json
import os
from datetime import datetime

class QueueManager:
    def __init__(self):
        self.queue_file = "reading_queue.json"
        self._ensure_queue_file()
    
    def _ensure_queue_file(self):
        """Creates queue file if it doesn't exist."""
        if not os.path.exists(self.queue_file):
            with open(self.queue_file, 'w') as f:
                json.dump({"queue": [], "completed": []}, f)
    
    def add_to_queue(self, client_email, order_note, reading_topic, target_length="8000"):
        """Adds a new reading request to the queue."""
        with open(self.queue_file, 'r') as f:
            data = json.load(f)
        
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
        
        data["queue"].append(new_item)
        
        with open(self.queue_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        return new_item["id"]
    
    def get_queue(self):
        """Returns all pending items in queue."""
        with open(self.queue_file, 'r') as f:
            data = json.load(f)
        return [item for item in data["queue"] if item["status"] == "pending"]
    
    def get_completed(self, limit=10):
        """Returns last N completed items."""
        with open(self.queue_file, 'r') as f:
            data = json.load(f)
        return data["completed"][-limit:]
    
    def mark_processing(self, item_id):
        """Marks an item as currently processing."""
        with open(self.queue_file, 'r') as f:
            data = json.load(f)
        
        for item in data["queue"]:
            if item["id"] == item_id:
                item["status"] = "processing"
                break
        
        with open(self.queue_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def mark_completed(self, item_id, pdf_path):
        """Moves item from queue to completed."""
        with open(self.queue_file, 'r') as f:
            data = json.load(f)
        
        # Find and remove from queue
        completed_item = None
        for i, item in enumerate(data["queue"]):
            if item["id"] == item_id:
                completed_item = data["queue"].pop(i)
                completed_item["status"] = "completed"
                completed_item["completed_at"] = datetime.now().isoformat()
                completed_item["pdf_path"] = pdf_path
                break
        
        if completed_item:
            data["completed"].append(completed_item)
        
        with open(self.queue_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def mark_failed(self, item_id, error_message):
        """Marks an item as failed."""
        with open(self.queue_file, 'r') as f:
            data = json.load(f)
        
        for item in data["queue"]:
            if item["id"] == item_id:
                item["status"] = "failed"
                item["error"] = error_message
                break
        
        with open(self.queue_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def clear_queue(self):
        """Clears all pending items from queue."""
        with open(self.queue_file, 'r') as f:
            data = json.load(f)
        
        data["queue"] = [item for item in data["queue"] if item["status"] != "pending"]
        
        with open(self.queue_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def get_stats(self):
        """Returns queue statistics."""
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
