"""Layer 1: Personal Assistant Agent implementation supporting both Google Antigravity SDK and Universal Gateway."""

import os
import json
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable

from gateway.config import load_env

load_env()

from assistant.memory import memory_store
from assistant.tools.calendar_tool import get_calendar_events, add_calendar_event
from assistant.tools.tasks_tool import list_tasks, add_task, complete_task
from assistant.tools.briefing_tool import generate_morning_briefing
from assistant.router import dispatch_to_specialist
from evolver.engine import self_evolver
from gateway.router import gateway
from rag import search_knowledge_base, index_file, list_indexed_documents
from mcp_hub import list_mcp_tools, call_mcp_tool
from swarm import swarm
from tools.browser import scrape_url, search_web

def get_system_health_and_evolution() -> str:
    """Checks the health of the Universal API Gateway and the current Self-Evolver version."""
    active_providers = gateway.get_active_providers()
    ev_summary = self_evolver.get_evolution_summary()
    return (
        f"[SYSTEM STATUS]\n"
        f"Active Gateway Providers: {', '.join(active_providers) if active_providers else 'None'}\n"
        f"{ev_summary}\n"
        f"{list_indexed_documents()}"
    )

def remember_fact_tool(fact: str) -> str:
    """Stores a new fact about the user in long-term persistent memory."""
    return memory_store.remember_fact(fact)

def update_user_profile_tool(key: str, value: str) -> str:
    """Updates a field in the user profile (e.g. 'name', 'timezone', 'primary_focus')."""
    return memory_store.update_profile(key, value)

TOOLS_REGISTRY: Dict[str, Callable] = {
    "get_calendar_events": get_calendar_events,
    "add_calendar_event": add_calendar_event,
    "list_tasks": list_tasks,
    "add_task": add_task,
    "complete_task": complete_task,
    "generate_morning_briefing": generate_morning_briefing,
    "remember_fact": remember_fact_tool,
    "update_user_profile": update_user_profile_tool,
    "dispatch_to_specialist": dispatch_to_specialist,
    "get_system_health": get_system_health_and_evolution,
    "search_knowledge_base": search_knowledge_base,
    "index_document": index_file,
    "list_indexed_documents": list_indexed_documents,
    "list_mcp_tools": list_mcp_tools,
    "call_mcp_tool": call_mcp_tool,
    "list_specialists": swarm.list_specialists,
    "run_swarm_workflow": swarm.run_collaborative_workflow,
    "scrape_url": scrape_url,
    "search_web": search_web,
}

def build_system_instructions() -> str:
    memory_block = memory_store.get_memory_prompt_block()
    
    return f"""You are Hermit Agent, the user's primary Personal AI Assistant (Layer 1).
You serve as an executive chief-of-staff, orchestrator, and personal copilot.

{memory_block}

### AVAILABLE TOOLS:
- get_calendar_events(day="YYYY-MM-DD" or omit for today)
- add_calendar_event(title, start_time, end_time, day=None, description="")
- list_tasks(status="pending" or "completed" or omit for all)
- add_task(description, priority="P1"|"P2"|"P3", due_date=None)
- complete_task(task_id="task-1")
- generate_morning_briefing()
- remember_fact(fact="user preference")
- update_user_profile(key="field", value="val")
- search_knowledge_base(query="term to search in documents")
- index_document(file_path="path/to/file")
- list_indexed_documents()
- list_mcp_tools()
- call_mcp_tool(server_name="system_info|filesystem", tool_name="name", arguments=None)
- dispatch_to_specialist(task_domain="domain", task_details="specs")
- list_specialists()
- run_swarm_workflow(objective="goal")
- scrape_url(url="https://...")
- search_web(query="terms")
- get_system_health()

### CORE OPERATING RULES:
1. Always be concise, structured, professional, and actionable.
2. If the user asks about their schedule, tasks, documents, knowledge base, system status, web content, or specialist delegation, use your tools.
   To call a tool, output: `[TOOL_CALL: tool_name(param="value")]`.
3. If no tool is needed, respond directly and helpfully.
"""

class UniversalGatewayAgent:
    """Agent implementation running across Universal Gateway providers (OpenRouter, Groq, etc.)."""

    def __init__(self, system_instructions: str):
        self.system_instructions = system_instructions
        self.history: List[Dict[str, str]] = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

    async def chat(self, prompt: str) -> str:
        # Intent heuristics for immediate context augmentation
        lower = prompt.lower()
        if "calendar" in lower or "meetings" in lower or "schedule" in lower:
            cal_data = get_calendar_events()
            prompt_context = f"{prompt}\n\n[Live Calendar Data]:\n{cal_data}"
        elif "tasks" in lower or "to-do" in lower or "todos" in lower:
            task_data = list_tasks()
            prompt_context = f"{prompt}\n\n[Live Tasks Data]:\n{task_data}"
        elif "briefing" in lower or "morning brief" in lower:
            return generate_morning_briefing()
        elif "health" in lower or "status" in lower:
            return get_system_health_and_evolution()
        elif "mcp" in lower or "servers" in lower or "server tools" in lower:
            mcp_data = list_mcp_tools()
            prompt_context = f"{prompt}\n\n[Connected MCP Tools]:\n{mcp_data}"
        elif any(k in lower for k in ["doc", "docs", "document", "knowledge", "rag", "search file"]):
            kb_data = search_knowledge_base(prompt)
            prompt_context = f"{prompt}\n\n[Knowledge Base Context]:\n{kb_data}"
        elif "scrape" in lower or "crawl" in lower or "http://" in lower or "https://" in lower:
            import re
            urls = re.findall(r'https?://[^\s]+', prompt)
            scraped = scrape_url(urls[0]) if urls else scrape_url(prompt.split()[-1])
            prompt_context = f"{prompt}\n\n[Scraped Web Page Content]:\n{scraped}"
        elif "search web" in lower or "google" in lower or "duckduckgo" in lower:
            query = prompt.replace("search web for", "").replace("search web", "").strip()
            web_results = search_web(query or prompt)
            prompt_context = f"{prompt}\n\n[Live Web Search Results]:\n{web_results}"
        elif "specialist" in lower or "swarm" in lower:
            if "list" in lower:
                return swarm.list_specialists()
            elif "workflow" in lower or "pipeline" in lower:
                return await swarm.run_collaborative_workflow(prompt)
            elif "research" in lower:
                return await swarm.dispatch("research", prompt)
            elif "code" in lower or "engineer" in lower:
                return await swarm.dispatch("code", prompt)
            elif "review" in lower or "qa" in lower:
                return await swarm.dispatch("review", prompt)
            prompt_context = f"{prompt}\n\n[Available Specialists]:\n{swarm.list_specialists()}"
        else:
            prompt_context = prompt

        response = await gateway.complete(
            prompt=prompt_context,
            system_instruction=self.system_instructions
        )
        return response.text.strip()

def create_personal_assistant() -> Any:
    """Instantiates the Layer 1 Personal Assistant.

    Uses Google Antigravity SDK if a valid GEMINI_API_KEY is present,
    otherwise uses the Universal Gateway (OpenRouter, Groq, etc.).
    """
    instructions = build_system_instructions()
    
    # If GEMINI_API_KEY is configured, try native Antigravity SDK
    if os.environ.get("GEMINI_API_KEY"):
        try:
            from google.antigravity import Agent, LocalAgentConfig
            from google.antigravity.hooks import policy
            from google.antigravity.models import DEFAULT_MODEL
            config = LocalAgentConfig(
                system_instructions=instructions,
                model=DEFAULT_MODEL,
                tools=list(TOOLS_REGISTRY.values()),
                policies=[policy.allow_all()],
            )
            return Agent(config)
        except Exception:
            pass

    # Default to Universal Gateway Agent (OpenRouter, Groq, etc.)
    return UniversalGatewayAgent(system_instructions=instructions)
