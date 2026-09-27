"""Layer 1: Personal Assistant Agent with a real tool-call execution loop.

The model emits `[TOOL_CALL: name(param="value")]`; we parse it, execute the
registered tool, feed the result back, and let the model continue - up to
MAX_TOOL_LOOPS rounds. Conversation history is kept per agent instance and
passed to the gateway so chat turns are not stateless.
"""

import os
import ast
import inspect
import re
from typing import Dict, Any, List, Optional, Callable, Tuple

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

MAX_TOOL_LOOPS = 5
HISTORY_LIMIT = 40  # messages passed to providers

# Matches [TOOL_CALL: name(...)] - one balanced paren level deep.
TOOL_CALL_RE = re.compile(
    r"\[TOOL_CALL:\s*([A-Za-z_][\w]*)\s*(\((?:[^()\[\]]|\([^()]*\))*\))?\s*\]"
)

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
2. To use a tool, output EXACTLY one line per call in this form:
   [TOOL_CALL: tool_name(param="value")]
   You may emit several calls. After tools run, you receive their results as
   [TOOL_RESULT: name] blocks and then give the final answer.
   Only emit tool calls when a tool is actually needed; otherwise answer directly.
3. When the user asks you to add, schedule, complete, remember, or update
   something, ALWAYS use the matching tool - never just say you did it.
"""

def parse_tool_call_args(arg_src: Optional[str]) -> Tuple[list, dict]:
    """Parses the argument list of a tool call using the Python AST.

    Only literal constants are allowed - no arbitrary code execution.
    """
    if not arg_src:
        return [], {}
    expr = ast.parse(f"__tool__{arg_src}", mode="eval").body
    args = [ast.literal_eval(a) for a in expr.args]
    kwargs = {kw.arg: ast.literal_eval(kw.value) for kw in expr.keywords}
    return args, kwargs

class UniversalGatewayAgent:
    """Agent implementation running across Universal Gateway providers (OpenRouter, Groq, etc.)."""

    def __init__(self, system_instructions: str):
        self.system_instructions = system_instructions
        self.history: List[Dict[str, str]] = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

    def apply_instructions(self, new_instructions: str):
        """Applies a mutated system prompt produced by the Self-Evolver."""
        if new_instructions and new_instructions.strip():
            self.system_instructions = new_instructions

    def _record_turn(self, user_text: str, assistant_text: str):
        self.history.append({"role": "user", "content": user_text})
        self.history.append({"role": "assistant", "content": assistant_text})
        if len(self.history) > HISTORY_LIMIT * 2:
            self.history = self.history[-HISTORY_LIMIT * 2:]

    async def _run_tool_call(self, name: str, arg_src: Optional[str]) -> str:
        fn = TOOLS_REGISTRY.get(name)
        if fn is None:
            known = ", ".join(sorted(TOOLS_REGISTRY))
            return f"[TOOL ERROR] Unknown tool '{name}'. Known tools: {known}"
        try:
            args, kwargs = parse_tool_call_args(arg_src)
        except Exception as e:
            return f"[TOOL ERROR] Could not parse arguments for '{name}': {e}"
        try:
            result = fn(*args, **kwargs)
            if inspect.isawaitable(result):
                result = await result
            return str(result)
        except TypeError as e:
            return f"[TOOL ERROR] Bad arguments for '{name}': {e}"
        except Exception as e:
            return f"[TOOL ERROR] {type(e).__name__} while running '{name}': {e}"

    def _fast_path(self, prompt: str) -> Optional[str]:
        """Deterministic shortcuts for read-only status queries."""
        lower = prompt.lower()
        if "briefing" in lower or "morning brief" in lower:
            return generate_morning_briefing()
        if "health" in lower or "status" in lower:
            return get_system_health_and_evolution()
        if "specialist" in lower and "list" in lower:
            return swarm.list_specialists()
        return None

    def _augment_context(self, prompt: str) -> str:
        """Injects live data for common read intents (kept from the original design)."""
        lower = prompt.lower()
        if "calendar" in lower or "meetings" in lower or "schedule" in lower:
            return f"{prompt}\n\n[Live Calendar Data]:\n{get_calendar_events()}"
        if "tasks" in lower or "to-do" in lower or "todos" in lower:
            return f"{prompt}\n\n[Live Tasks Data]:\n{list_tasks()}"
        if "mcp" in lower or "servers" in lower or "server tools" in lower:
            return f"{prompt}\n\n[Connected MCP Tools]:\n{list_mcp_tools()}"
        if any(k in lower for k in ["doc", "docs", "document", "knowledge", "rag", "search file"]):
            return f"{prompt}\n\n[Knowledge Base Context]:\n{search_knowledge_base(prompt)}"
        if "scrape" in lower or "crawl" in lower or "http://" in lower or "https://" in lower:
            urls = re.findall(r'https?://[^\s]+', prompt)
            scraped = scrape_url(urls[0]) if urls else "[No URL found in message]"
            return f"{prompt}\n\n[Scraped Web Page Content]:\n{scraped}"
        if "search web" in lower or "duckduckgo" in lower:
            query = prompt.replace("search web for", "").replace("search web", "").strip()
            return f"{prompt}\n\n[Live Web Search Results]:\n{search_web(query or prompt)}"
        return prompt

    async def chat(self, prompt: str) -> str:
        fast = self._fast_path(prompt)
        if fast is not None:
            self._record_turn(prompt, fast)
            return fast

        # Swarm dispatch shortcuts (async, explicit)
        lower = prompt.lower()
        if "swarm" in lower or "specialist" in lower:
            if "workflow" in lower or "pipeline" in lower:
                reply = await swarm.run_collaborative_workflow(prompt)
                self._record_turn(prompt, reply)
                return reply
            if "research" in lower:
                reply = await swarm.dispatch("research", prompt)
                self._record_turn(prompt, reply)
                return reply

        working_prompt = self._augment_context(prompt)
        history_snapshot = list(self.history)[-HISTORY_LIMIT:]

        last_text = ""
        for _ in range(MAX_TOOL_LOOPS):
            response = await gateway.complete(
                prompt=working_prompt,
                system_instruction=self.system_instructions,
                history=history_snapshot,
            )
            text = response.text.strip()
            last_text = text

            calls = TOOL_CALL_RE.findall(text)
            if not calls:
                self._record_turn(prompt, text)
                return text

            # Execute every requested tool call, then feed results back.
            results = []
            for name, arg_src in calls:
                output = await self._run_tool_call(name, arg_src)
                results.append(f"[TOOL_RESULT: {name}]\n{output}")

            history_snapshot.append({"role": "user", "content": working_prompt})
            history_snapshot.append({"role": "assistant", "content": text})
            working_prompt = (
                "The tool calls you requested have been executed. Results:\n\n"
                + "\n\n".join(results)
                + "\n\nNow either issue more [TOOL_CALL: ...] lines if needed, "
                  "or give the user the final answer."
            )

        # Loop cap reached - return whatever the model last said, with the run note.
        note = last_text + "\n\n[Note: tool-call round limit reached]"
        self._record_turn(prompt, note)
        return note

def create_personal_assistant() -> Any:
    """Instantiates the Layer 1 Personal Assistant.

    Uses Google Antigravity SDK if a valid GEMINI_API_KEY is present,
    otherwise uses the Universal Gateway (OpenRouter, Groq, etc.).
    """
    instructions = build_system_instructions()

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

    return UniversalGatewayAgent(system_instructions=instructions)
