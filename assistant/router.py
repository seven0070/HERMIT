"""Router / Dispatcher for Layer 1.

Classifies incoming user intent:
- DIRECT_ASSISTANCE: Calendar, tasks, memory, general questions, daily briefings (handled by Layer 1).
- DELEGATE_SPECIALIST: Deep research, software engineering, QA reviews, complex multi-stage workflows (handled by Layer 4 Swarm).
"""

import asyncio
from typing import Dict, Any, Optional
from swarm.orchestrator import swarm

async def dispatch_to_specialist_async(task_domain: str, task_details: str, context: Optional[str] = None) -> str:
    """Dispatches a task to a Layer 4 Specialist Agent and returns the execution report."""
    return await swarm.dispatch(task_domain, task_details, context=context)

def dispatch_to_specialist(task_domain: str, task_details: str) -> str:
    """Sync wrapper to dispatch task to a Layer 4 Specialist Agent."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If in running loop, schedule as future or run in executor
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                result = pool.submit(asyncio.run, swarm.dispatch(task_domain, task_details)).result()
                return result
        else:
            return loop.run_until_complete(swarm.dispatch(task_domain, task_details))
    except Exception as e:
        return f"[SWARM DISPATCH NOTE] Task routed to '{task_domain.upper()}': {task_details}. (Dispatched to swarm: {e})"
