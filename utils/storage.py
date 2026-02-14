import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime
from config import config


class JSONStorage:
    """Handle JSON file operations for local storage"""

    def __init__(self, filename: str):
        self.filepath = config.DATA_DIR / filename
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        """Create file with empty structure if it doesn't exist"""
        if not self.filepath.exists():
            self.write({})

    def read(self) -> Dict[str, Any]:
        """Read data from JSON file"""
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}

    def write(self, data: Dict[str, Any]):
        """Write data to JSON file"""
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def append_item(self, key: str, item: Any):
        """Append item to a list in JSON"""
        data = self.read()
        if key not in data:
            data[key] = []
        data[key].append(item)
        self.write(data)

    def update_field(self, key: str, value: Any):
        """Update a specific field"""
        data = self.read()
        data[key] = value
        self.write(data)


class ConversationStorage:
    """Manage conversation history"""

    def __init__(self):
        self.storage = JSONStorage("conversations.json")

    def save_conversation(self, session_id: str, message: Dict[str, Any]):
        """Save a conversation message"""
        data = self.storage.read()

        if session_id not in data:
            data[session_id] = {
                "created_at": datetime.now().isoformat(),
                "messages": [],
            }

        message["timestamp"] = datetime.now().isoformat()
        data[session_id]["messages"].append(message)

        # Limit history size
        if len(data[session_id]["messages"]) > config.max_conversation_history:
            data[session_id]["messages"] = data[session_id]["messages"][
                -config.max_conversation_history :
            ]

        self.storage.write(data)

    def get_conversation(self, session_id: str) -> List[Dict[str, Any]]:
        """Retrieve conversation history"""
        data = self.storage.read()
        return data.get(session_id, {}).get("messages", [])

    def list_sessions(self) -> List[str]:
        """List all conversation sessions"""
        data = self.storage.read()
        return list(data.keys())

    def delete_session(self, session_id: str):
        """Delete a conversation session"""
        data = self.storage.read()
        if session_id in data:
            del data[session_id]
            self.storage.write(data)
