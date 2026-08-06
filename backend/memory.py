import json
import os
import re
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Optional

class SessionMemory:
    """Manages chat history and active schedule state for the Railway Copilot."""
    def __init__(self, session_id: str = "default", storage_file: Optional[str] = None):
        """Create isolated, durable state for one UI session.

        A caller-supplied file remains supported for migration/tests.  Otherwise
        session data lives under the repository's data/sessions directory rather
        than in a single shared file for every Streamlit visitor.
        """
        base_dir = Path(__file__).resolve().parent.parent / "data" / "sessions"
        safe_session_id = re.sub(r"[^A-Za-z0-9_-]", "_", session_id)[:128] or "default"
        self.storage_file = storage_file or str(base_dir / f"{safe_session_id}.json")
        self.chat_history: List[Dict[str, str]] = []
        self.active_scenario: Optional[str] = None
        self.current_schedule: Optional[List[Dict[str, Any]]] = None
        self.load_state()

    def add_message(self, role: str, content: str):
        self.chat_history.append({"role": role, "content": content})
        self.save_state()

    def get_history(self) -> List[Dict[str, str]]:
        return self.chat_history

    def update_schedule_state(self, scenario_name: str, schedule: List[Dict[str, Any]]):
        self.active_scenario = scenario_name
        self.current_schedule = schedule
        self.save_state()

    def clear(self):
        self.chat_history = []
        self.active_scenario = None
        self.current_schedule = None
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except Exception:
                pass

    def save_state(self):
        try:
            os.makedirs(os.path.dirname(self.storage_file), exist_ok=True)
            # Atomic replace prevents readers from observing a partially-written
            # JSON document after a browser refresh or interrupted process.
            fd, temp_path = tempfile.mkstemp(
                dir=os.path.dirname(self.storage_file), suffix=".tmp", text=True
            )
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump({
                    "chat_history": self.chat_history,
                    "active_scenario": self.active_scenario,
                    "current_schedule": self.current_schedule
                }, f, indent=2)
            os.replace(temp_path, self.storage_file)
        except Exception as e:
            print(f"Warning: Failed to save session memory: {e}")

    def load_state(self):
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.chat_history = data.get("chat_history", [])
                    self.active_scenario = data.get("active_scenario")
                    self.current_schedule = data.get("current_schedule")
            except Exception:
                pass
