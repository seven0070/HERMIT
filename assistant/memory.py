import json
import os
from pathlib import Path
from typing import Any, Dict

DEFAULT_DATA_DIR = Path(__file__).resolve().parent.parent / "data"
MEMORY_FILE = DEFAULT_DATA_DIR / "user_memory.json"

DEFAULT_MEMORY: Dict[str, Any] = {
    "user_profile": {
        "name": "User",
        "timezone": "UTC",
        "communication_style": "Concise, actionable, and structured",
        "primary_focus": "Building AI agents and software systems",
        "preferences": {}
    },
    "facts": [
        "Prefers concise answers with direct action steps.",
        "Interested in building multi-layered AI agent systems."
    ],
    "context_notes": []
}

class MemoryStore:
    """Persistent memory store inspired by Letta/MemGPT memory blocks."""

    def __init__(self, file_path: Path = MEMORY_FILE):
        self.file_path = file_path
        self._ensure_storage()

    def _ensure_storage(self):
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.file_path.exists():
            self.save(DEFAULT_MEMORY)

    def load(self) -> Dict[str, Any]:
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return DEFAULT_MEMORY

    def save(self, data: Dict[str, Any]):
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def get_memory_prompt_block(self) -> str:
        """Formats the persistent memory into a system prompt section."""
        data = self.load()
        profile = data.get("user_profile", {})
        facts = data.get("facts", [])
        
        prompt = "## USER PROFILE & PERSISTENT MEMORY\n"
        prompt += f"- Name: {profile.get('name', 'User')}\n"
        prompt += f"- Timezone: {profile.get('timezone', 'UTC')}\n"
        prompt += f"- Primary Focus: {profile.get('primary_focus', 'N/A')}\n"
        prompt += f"- Communication Style: {profile.get('communication_style', 'Concise')}\n"
        
        if facts:
            prompt += "\n### Stored Facts About User:\n"
            for fact in facts:
                prompt += f"- {fact}\n"
                
        return prompt

    def remember_fact(self, fact: str) -> str:
        """Stores a new fact about the user for future conversations."""
        data = self.load()
        if fact not in data["facts"]:
            data["facts"].append(fact)
            self.save(data)
            return f"Remembered: '{fact}'"
        return "Fact already known."

    def update_profile(self, key: str, value: str) -> str:
        """Updates a user profile field (e.g., name, timezone, primary_focus)."""
        data = self.load()
        data["user_profile"][key] = value
        self.save(data)
        return f"Updated profile field '{key}' to '{value}'."

    def get_profile(self) -> Dict[str, Any]:
        return self.load().get("user_profile", {})

    def get_facts(self) -> list:
        return self.load().get("facts", [])

memory_store = MemoryStore()

