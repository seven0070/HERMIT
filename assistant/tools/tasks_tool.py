import json
from datetime import date
from pathlib import Path
from typing import List, Dict, Any, Optional

DEFAULT_DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
TASKS_FILE = DEFAULT_DATA_DIR / "tasks.json"

class TaskStore:
    """Persistent task tracker for daily action items and priorities."""

    def __init__(self, file_path: Path = TASKS_FILE):
        self.file_path = file_path
        self._ensure_storage()

    def _ensure_storage(self):
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.file_path.exists():
            sample_tasks = [
                {
                    "id": "task-1",
                    "description": "Define Layer 1 personal assistant architecture",
                    "priority": "P1",
                    "status": "in_progress",
                    "due_date": str(date.today())
                },
                {
                    "id": "task-2",
                    "description": "Connect prebuilt tools from awesome-ai-apps & awesome-llm-apps",
                    "priority": "P1",
                    "status": "pending",
                    "due_date": str(date.today())
                }
            ]
            self.save(sample_tasks)

    def load(self) -> List[Dict[str, Any]]:
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def save(self, tasks: List[Dict[str, Any]]):
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(tasks, f, indent=2, ensure_ascii=False)

task_store = TaskStore()

def list_tasks(status: Optional[str] = None) -> str:
    """Lists current to-do tasks.
    
    Args:
        status: Optional filter by status ('pending', 'in_progress', 'completed').
    """
    tasks = task_store.load()
    if status:
        tasks = [t for t in tasks if t.get("status") == status]
        
    if not tasks:
        return "No tasks found."
        
    output = "Tasks:\n"
    for t in tasks:
        output += f"- [{t.get('priority', 'P2')}] [{t.get('status')}] #{t.get('id')}: {t.get('description')} (Due: {t.get('due_date', 'N/A')})\n"
    return output.strip()

def add_task(description: str, priority: str = "P2", due_date: Optional[str] = None) -> str:
    """Adds a new task to your personal task list.
    
    Args:
        description: Description of the task.
        priority: Priority level ('P1' high, 'P2' medium, 'P3' low). Default 'P2'.
        due_date: Optional due date (YYYY-MM-DD). Defaults to today.
    """
    tasks = task_store.load()
    new_task = {
        "id": f"task-{len(tasks) + 1}",
        "description": description,
        "priority": priority.upper(),
        "status": "pending",
        "due_date": due_date if due_date else str(date.today())
    }
    tasks.append(new_task)
    task_store.save(tasks)
    return f"Created task #{new_task['id']} [{new_task['priority']}]: {description}"

def complete_task(task_id: str) -> str:
    """Marks a task as completed.
    
    Args:
        task_id: The ID of the task (e.g. 'task-1' or '1').
    """
    clean_id = task_id if task_id.startswith("task-") else f"task-{task_id}"
    tasks = task_store.load()
    for t in tasks:
        if t.get("id") == clean_id:
            t["status"] = "completed"
            task_store.save(tasks)
            return f"Task #{clean_id} marked as completed."
    return f"Task #{clean_id} not found."
