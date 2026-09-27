import json
from datetime import datetime, date
from pathlib import Path
from typing import List, Dict, Any, Optional

DEFAULT_DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
CALENDAR_FILE = DEFAULT_DATA_DIR / "calendar_events.json"

class CalendarStore:
    """Local calendar store with Google Calendar compatible event schema."""

    def __init__(self, file_path: Path = CALENDAR_FILE):
        self.file_path = file_path
        self._ensure_storage()

    def _ensure_storage(self):
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.file_path.exists():
            sample_events = [
                {
                    "id": "evt-1",
                    "title": "Agent Architecture Sync",
                    "date": str(date.today()),
                    "start_time": "10:00",
                    "end_time": "10:30",
                    "description": "Align on Layer 1 Personal Assistant and Layer 2 Specialists",
                    "attendees": ["Team"]
                },
                {
                    "id": "evt-2",
                    "title": "Deep Research Sprint",
                    "date": str(date.today()),
                    "start_time": "14:00",
                    "end_time": "15:00",
                    "description": "Review data extraction benchmarks",
                    "attendees": ["Solo"]
                }
            ]
            self.save(sample_events)

    def load(self) -> List[Dict[str, Any]]:
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def save(self, events: List[Dict[str, Any]]):
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(events, f, indent=2, ensure_ascii=False)

calendar_store = CalendarStore()

def get_calendar_events(day: Optional[str] = None) -> str:
    """Lists calendar events for a specific date (YYYY-MM-DD) or today if omitted.
    
    Args:
        day: Optional date string in YYYY-MM-DD format. Defaults to today's date.
    """
    target_date = day if day else str(date.today())
    events = calendar_store.load()
    filtered = [e for e in events if e.get("date") == target_date]
    
    if not filtered:
        return f"No events scheduled for {target_date}."
    
    output = f"Events for {target_date}:\n"
    for e in filtered:
        output += f"- [{e.get('start_time')} - {e.get('end_time')}] {e.get('title')} ({e.get('description', '')})\n"
    return output.strip()

def add_calendar_event(
    title: str,
    start_time: str,
    end_time: str,
    day: Optional[str] = None,
    description: str = "",
    attendees: Optional[List[str]] = None
) -> str:
    """Adds a new event or meeting to the calendar.
    
    Args:
        title: Title or summary of the meeting/event.
        start_time: Start time (e.g. '11:00').
        end_time: End time (e.g. '12:00').
        day: Date in YYYY-MM-DD format. Defaults to today.
        description: Optional notes or description.
        attendees: Optional list of attendees.
    """
    target_date = day if day else str(date.today())
    events = calendar_store.load()
    new_event = {
        "id": f"evt-{len(events) + 1}",
        "title": title,
        "date": target_date,
        "start_time": start_time,
        "end_time": end_time,
        "description": description,
        "attendees": attendees or []
    }
    events.append(new_event)
    calendar_store.save(events)
    return f"Successfully scheduled '{title}' on {target_date} from {start_time} to {end_time}."
