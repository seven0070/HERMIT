from datetime import date
from assistant.memory import memory_store
from assistant.tools.calendar_tool import calendar_store
from assistant.tools.tasks_tool import task_store

def generate_morning_briefing() -> str:
    """Generates an executive daily briefing consolidating calendar events, top tasks, and active priorities."""
    today_str = str(date.today())
    mem = memory_store.load()
    profile = mem.get("user_profile", {})
    
    # 1. Calendar
    events = [e for e in calendar_store.load() if e.get("date") == today_str]
    
    # 2. Tasks
    pending_tasks = [t for t in task_store.load() if t.get("status") in ("pending", "in_progress")]
    p1_tasks = [t for t in pending_tasks if t.get("priority") == "P1"]
    
    # Format briefing
    briefing = [
        "=" * 56,
        f"DAILY BRIEFING -- {today_str}",
        f"User: {profile.get('name', 'User')} | Focus: {profile.get('primary_focus', 'AI Development')}",
        "=" * 56,
        f"\n[SCHEDULE] TODAY'S CALENDAR ({len(events)} event{'s' if len(events) != 1 else ''}):"
    ]
    
    if events:
        for e in events:
            briefing.append(f"  * [{e.get('start_time')} - {e.get('end_time')}] {e.get('title')}")
    else:
        briefing.append("  * No meetings scheduled today. Open focus time!")
        
    briefing.append(f"\n[PRIORITIES] ACTIVE TASKS ({len(p1_tasks)} urgent / {len(pending_tasks)} total pending):")
    if pending_tasks:
        for t in pending_tasks[:5]:
            badge = "[P1-URGENT]" if t.get("priority") == "P1" else f"[{t.get('priority')}]"
            briefing.append(f"  * {badge} #{t.get('id')}: {t.get('description')}")
    else:
        briefing.append("  * All tasks completed! Ready for new objectives.")
        
    briefing.append(f"\n[ASSISTANT NOTE]")
    briefing.append("  * Layer 1 Personal Assistant is active and ready to assist or dispatch to specialist agents.")
    briefing.append("=" * 56)
    
    return "\n".join(briefing)
