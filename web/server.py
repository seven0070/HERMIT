"""Modern Web UI and REST API server for AI Multi-Layer Agent System."""

import os
import json
import asyncio
from pathlib import Path
from starlette.applications import Starlette
from starlette.responses import HTMLResponse, JSONResponse
from starlette.routing import Route
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware

from gateway.config import load_env

load_env()

from assistant.agent import create_personal_assistant
from assistant.memory import memory_store
from assistant.tools.calendar_tool import get_calendar_events, add_calendar_event, calendar_store
from assistant.tools.tasks_tool import list_tasks, add_task, complete_task, task_store
from assistant.tools.briefing_tool import generate_morning_briefing
from gateway.router import gateway
from evolver.engine import self_evolver
from rag import search_knowledge_base, list_indexed_documents, index_file
from rag.store import doc_store
from mcp_hub import list_mcp_tools, call_mcp_tool
from swarm import swarm

# Global assistant instance
_assistant = create_personal_assistant()

async def api_status(request):
    """Returns comprehensive system health across all 4 layers."""
    return JSONResponse({
        "status": "healthy",
        "gateway": {
            "active_providers": gateway.get_active_providers(),
            "default_model": os.environ.get("DEFAULT_UNIVERSAL_MODEL", "nvidia/nemotron-3.5-lightning:free")
        },
        "evolver": {
            "version": self_evolver.get_current_version(),
            "summary": self_evolver.get_evolution_summary(),
            "history": self_evolver.get_history()
        },
        "memory": {
            "profile": memory_store.get_profile(),
            "facts": memory_store.get_facts()
        },
        "rag": {
            "indexed_files": [d.get("filename") for d in doc_store.get_documents()],
            "total_chunks": len(doc_store.get_all_chunks())
        }
    })

async def api_chat(request):
    """Processes user chat messages through the 4-layer agent pipeline."""
    try:
        body = await request.json()
        message = body.get("message", "").strip()
        if not message:
            return JSONResponse({"error": "Empty message"}, status_code=400)

        async with _assistant as ag:
            reply = await ag.chat(message)

        # Autonomous Layer 2 evolution check
        ev_res = await self_evolver.evolve(
            current_instructions="",
            user_input=message,
            agent_output=reply
        )

        return JSONResponse({
            "reply": reply,
            "evolution": ev_res
        })
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

async def api_briefing(request):
    """Returns daily executive morning briefing."""
    return JSONResponse({"briefing": generate_morning_briefing()})

async def api_tasks(request):
    """Lists or adds tasks."""
    if request.method == "GET":
        return JSONResponse({"tasks": task_store.get_all_tasks()})
    elif request.method == "POST":
        data = await request.json()
        desc = data.get("description", "")
        priority = data.get("priority", "P2")
        due = data.get("due_date")
        task = task_store.add_task(desc, priority=priority, due_date=due)
        return JSONResponse({"task": task})

async def api_complete_task(request):
    """Marks a task as completed."""
    data = await request.json()
    task_id = data.get("task_id", "")
    success = task_store.complete_task(task_id)
    return JSONResponse({"success": success})

async def api_calendar(request):
    """Lists or adds calendar events."""
    if request.method == "GET":
        day = request.query_params.get("day")
        return JSONResponse({"events": calendar_store.get_events(day)})
    elif request.method == "POST":
        data = await request.json()
        ev = calendar_store.add_event(
            title=data.get("title", "Untitled"),
            start_time=data.get("start_time", "09:00"),
            end_time=data.get("end_time", "10:00"),
            day=data.get("day"),
            description=data.get("description", "")
        )
        return JSONResponse({"event": ev})

async def api_rag_search(request):
    """Queries the knowledge base."""
    q = request.query_params.get("q", "")
    results = search_knowledge_base(q)
    return JSONResponse({"query": q, "results": results})

async def api_rag_index(request):
    """Indexes a document file into the knowledge base."""
    data = await request.json()
    path = data.get("file_path", "")
    res = index_file(path)
    return JSONResponse({"result": res})

async def api_mcp_tools(request):
    """Lists all available MCP tools."""
    return JSONResponse({"tools": list_mcp_tools()})

async def api_mcp_execute(request):
    """Executes a specific MCP tool."""
    data = await request.json()
    server = data.get("server_name")
    tool = data.get("tool_name")
    args = data.get("arguments", {})
    res = call_mcp_tool(server, tool, args)
    return JSONResponse({"result": res})

async def api_swarm_collaborate(request):
    """Runs a 3-stage autonomous Swarm collaborative workflow."""
    data = await request.json()
    goal = data.get("objective", "")
    if not goal:
        return JSONResponse({"error": "Missing objective"}, status_code=400)
    report = await swarm.run_collaborative_workflow(goal)
    return JSONResponse({"report": report})

HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Hermit Agent - Command Center</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg: #090d16;
      --surface: #101626;
      --surface-border: #1f293d;
      --card-bg: rgba(19, 27, 46, 0.7);
      --primary: #6366f1;
      --primary-hover: #4f46e5;
      --primary-glow: rgba(99, 102, 241, 0.25);
      --accent: #06b6d4;
      --success: #10b981;
      --warning: #f59e0b;
      --text: #f1f5f9;
      --text-muted: #94a3b8;
      --radius: 12px;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: 'Plus Jakarta Sans', sans-serif;
      background-color: var(--bg);
      color: var(--text);
      display: flex;
      height: 100vh;
      overflow: hidden;
    }
    /* Sidebar */
    .sidebar {
      width: 270px;
      background: var(--surface);
      border-right: 1px solid var(--surface-border);
      display: flex;
      flex-direction: column;
      padding: 24px 16px;
      gap: 20px;
      flex-shrink: 0;
    }
    .brand {
      display: flex;
      align-items: center;
      gap: 12px;
      padding-bottom: 16px;
      border-bottom: 1px solid var(--surface-border);
    }
    .brand-icon {
      width: 38px;
      height: 38px;
      background: linear-gradient(135deg, #6366f1, #06b6d4);
      border-radius: 10px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 700;
      font-size: 18px;
    }
    .brand-title { font-weight: 700; font-size: 16px; }
    .brand-subtitle { font-size: 11px; color: var(--text-muted); }
    .nav-tabs { display: flex; flex-direction: column; gap: 6px; }
    .nav-btn {
      background: transparent;
      border: 1px solid transparent;
      color: var(--text-muted);
      padding: 10px 14px;
      border-radius: 8px;
      text-align: left;
      font-size: 13.5px;
      font-weight: 500;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 10px;
      transition: all 0.2s;
    }
    .nav-btn:hover { background: rgba(255,255,255,0.04); color: var(--text); }
    .nav-btn.active {
      background: var(--primary-glow);
      border-color: rgba(99, 102, 241, 0.4);
      color: #fff;
    }
    .sidebar-footer {
      margin-top: auto;
      padding: 12px;
      background: rgba(0,0,0,0.25);
      border-radius: var(--radius);
      font-size: 12px;
      border: 1px solid var(--surface-border);
    }
    .status-badge {
      display: inline-block;
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: var(--success);
      margin-right: 6px;
      box-shadow: 0 0 8px var(--success);
    }
    /* Main Content */
    .main {
      flex: 1;
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }
    .header {
      height: 64px;
      border-bottom: 1px solid var(--surface-border);
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0 28px;
      background: rgba(16, 22, 38, 0.5);
      backdrop-filter: blur(10px);
    }
    .header-title { font-size: 16px; font-weight: 600; }
    .header-pills { display: flex; gap: 10px; font-size: 12px; }
    .pill {
      background: rgba(255,255,255,0.05);
      border: 1px solid var(--surface-border);
      padding: 4px 12px;
      border-radius: 20px;
      color: var(--text-muted);
    }
    .content-area {
      flex: 1;
      overflow-y: auto;
      padding: 24px 28px;
    }
    .tab-content { display: none; }
    .tab-content.active { display: block; }
    /* Chat Tab */
    .chat-container {
      display: flex;
      flex-direction: column;
      height: calc(100vh - 120px);
      max-width: 900px;
      margin: 0 auto;
      background: var(--surface);
      border: 1px solid var(--surface-border);
      border-radius: var(--radius);
      overflow: hidden;
    }
    .chat-messages {
      flex: 1;
      padding: 20px;
      overflow-y: auto;
      display: flex;
      flex-direction: column;
      gap: 16px;
    }
    .message {
      display: flex;
      flex-direction: column;
      max-width: 80%;
      padding: 14px 18px;
      border-radius: 14px;
      font-size: 14px;
      line-height: 1.5;
    }
    .message.user {
      align-self: flex-end;
      background: var(--primary);
      color: white;
      border-bottom-right-radius: 4px;
    }
    .message.assistant {
      align-self: flex-start;
      background: rgba(255,255,255,0.05);
      border: 1px solid var(--surface-border);
      border-bottom-left-radius: 4px;
      white-space: pre-wrap;
    }
    .chat-input-bar {
      padding: 16px;
      border-top: 1px solid var(--surface-border);
      display: flex;
      gap: 10px;
      background: rgba(0,0,0,0.2);
    }
    .chat-input {
      flex: 1;
      background: var(--bg);
      border: 1px solid var(--surface-border);
      border-radius: 8px;
      padding: 12px 16px;
      color: white;
      font-size: 14px;
      outline: none;
    }
    .chat-input:focus { border-color: var(--primary); }
    .btn {
      background: var(--primary);
      color: white;
      border: none;
      border-radius: 8px;
      padding: 0 20px;
      font-weight: 600;
      font-size: 14px;
      cursor: pointer;
      transition: background 0.2s;
    }
    .btn:hover { background: var(--primary-hover); }
    /* Grid cards */
    .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px; margin-bottom: 24px; }
    .card {
      background: var(--card-bg);
      border: 1px solid var(--surface-border);
      border-radius: var(--radius);
      padding: 20px;
      backdrop-filter: blur(8px);
    }
    .card-title { font-size: 14px; font-weight: 600; color: var(--text-muted); margin-bottom: 12px; text-transform: uppercase; letter-spacing: 0.5px; }
    .card-stat { font-size: 24px; font-weight: 700; color: white; margin-bottom: 6px; }
    .code-box {
      background: #060911;
      border: 1px solid var(--surface-border);
      border-radius: 8px;
      padding: 14px;
      font-family: 'JetBrains Mono', monospace;
      font-size: 12px;
      overflow-x: auto;
      white-space: pre-wrap;
      color: #38bdf8;
    }
    /* List tables */
    .item-list { display: flex; flex-direction: column; gap: 8px; }
    .list-item {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 10px 14px;
      background: rgba(255,255,255,0.02);
      border: 1px solid var(--surface-border);
      border-radius: 8px;
      font-size: 13.5px;
    }
    .badge {
      padding: 2px 8px;
      border-radius: 12px;
      font-size: 11px;
      font-weight: 600;
    }
    .badge-p1 { background: rgba(239, 68, 68, 0.2); color: #ef4444; border: 1px solid #ef4444; }
    .badge-p2 { background: rgba(245, 158, 11, 0.2); color: #f59e0b; border: 1px solid #f59e0b; }
    .badge-p3 { background: rgba(16, 185, 129, 0.2); color: #10b981; border: 1px solid #10b981; }
  </style>
</head>
<body>

  <!-- Sidebar -->
  <div class="sidebar">
    <div class="brand">
      <div class="brand-icon">HA</div>
      <div>
        <div class="brand-title">Hermit Agent</div>
        <div class="brand-subtitle">Autonomous Multi-Layer Copilot</div>
      </div>
    </div>

    <div class="nav-tabs">
      <button class="nav-btn active" onclick="switchTab('chat')">💬 Personal Chat</button>
      <button class="nav-btn" onclick="switchTab('overview')">📊 Overview & Briefing</button>
      <button class="nav-btn" onclick="switchTab('swarm')">🤖 Multi-Agent Swarm</button>
      <button class="nav-btn" onclick="switchTab('tasks')">📅 Tasks & Calendar</button>
      <button class="nav-btn" onclick="switchTab('rag')">📚 Knowledge Base (RAG)</button>
      <button class="nav-btn" onclick="switchTab('mcp')">🔌 MCP Tool Explorer</button>
      <button class="nav-btn" onclick="switchTab('evolution')">🧬 Self-Evolution</button>
    </div>

    <div class="sidebar-footer">
      <div><span class="status-badge"></span>Universal Gateway Active</div>
      <div style="color: var(--text-muted); margin-top: 4px; font-size: 11px;">OpenRouter Auto-Failover</div>
    </div>
  </div>

  <!-- Main Content -->
  <div class="main">
    <div class="header">
      <div class="header-title" id="pageTitle">Personal Assistant Chat</div>
      <div class="header-pills">
        <div class="pill" id="pillModel">Model: nemotron-3.5:free</div>
        <div class="pill" id="pillVersion">Version: v1.0.0</div>
      </div>
    </div>

    <div class="content-area">

      <!-- 1. CHAT TAB -->
      <div id="tab-chat" class="tab-content active">
        <div class="chat-container">
          <div class="chat-messages" id="chatMessages">
            <div class="message assistant">Hello! I am Hermit Agent, your autonomous multi-layer copilot.
I can manage your calendar, prioritize your tasks, query the RAG knowledge base, scrape websites, search the web, execute MCP tools, or dispatch complex jobs to the Autonomous Multi-Agent Swarm. How can I assist you right now?</div>
          </div>
          <div class="chat-input-bar">
            <input type="text" id="chatInput" class="chat-input" placeholder="Type a message, ask about docs, schedule an event, or run a swarm..." onkeydown="if(event.key==='Enter') sendMessage()">
            <button class="btn" onclick="sendMessage()">Send</button>
          </div>
        </div>
      </div>

      <!-- 2. OVERVIEW TAB -->
      <div id="tab-overview" class="tab-content">
        <div class="grid">
          <div class="card">
            <div class="card-title">Gateway Status</div>
            <div class="card-stat" id="statGateway">Active</div>
            <div style="color: var(--text-muted); font-size: 13px;" id="statGatewayDetails">Loading...</div>
          </div>
          <div class="card">
            <div class="card-title">Self-Evolver</div>
            <div class="card-stat" id="statVersion">v1.0.0</div>
            <div style="color: var(--text-muted); font-size: 13px;" id="statEvolver">0 mutations</div>
          </div>
          <div class="card">
            <div class="card-title">RAG Knowledge</div>
            <div class="card-stat" id="statRAG">1 doc</div>
            <div style="color: var(--text-muted); font-size: 13px;" id="statRAGChunks">9 indexed chunks</div>
          </div>
        </div>

        <div class="card" style="margin-bottom: 24px;">
          <div class="card-title">Daily Executive Briefing</div>
          <div class="code-box" id="briefingBox" style="color: #f1f5f9; font-family: inherit; font-size: 13.5px; line-height: 1.6;">Loading morning briefing...</div>
        </div>
      </div>

      <!-- 3. SWARM TAB -->
      <div id="tab-swarm" class="tab-content">
        <div class="card" style="margin-bottom: 20px;">
          <div class="card-title">Collaborative Autonomous Swarm (Layer 4)</div>
          <p style="color: var(--text-muted); font-size: 13.5px; margin-bottom: 16px;">
            Executes a 3-agent pipeline: <strong>Researcher</strong> (facts/RAG) &rarr; <strong>Coder</strong> (architecture/code) &rarr; <strong>Reviewer</strong> (QA score & audit).
          </p>
          <div style="display: flex; gap: 10px;">
            <input type="text" id="swarmGoal" class="chat-input" placeholder="Enter objective (e.g. Design an automated webhook dispatcher for tasks)...">
            <button class="btn" onclick="runSwarm()">Run Pipeline</button>
          </div>
        </div>
        <div class="card">
          <div class="card-title">Swarm Pipeline Execution Log</div>
          <div class="code-box" id="swarmOutput">Ready to dispatch tasks to specialists...</div>
        </div>
      </div>

      <!-- 4. TASKS & CALENDAR TAB -->
      <div id="tab-tasks" class="tab-content">
        <div class="grid">
          <div class="card">
            <div class="card-title">Pending Tasks</div>
            <div class="item-list" id="tasksList">Loading tasks...</div>
          </div>
          <div class="card">
            <div class="card-title">Scheduled Calendar Events</div>
            <div class="item-list" id="calendarList">Loading calendar...</div>
          </div>
        </div>
      </div>

      <!-- 5. RAG TAB -->
      <div id="tab-rag" class="tab-content">
        <div class="card" style="margin-bottom: 20px;">
          <div class="card-title">Search Knowledge Base (Hybrid RAG)</div>
          <div style="display: flex; gap: 10px;">
            <input type="text" id="ragQuery" class="chat-input" placeholder="Search indexed documentation chunks..." onkeydown="if(event.key==='Enter') searchRAG()">
            <button class="btn" onclick="searchRAG()">Search</button>
          </div>
        </div>
        <div class="card">
          <div class="card-title">Search Results</div>
          <div class="code-box" id="ragResults">Enter a query above to test RAG retrieval...</div>
        </div>
      </div>

      <!-- 6. MCP TAB -->
      <div id="tab-mcp" class="tab-content">
        <div class="card" style="margin-bottom: 20px;">
          <div class="card-title">Connected Model Context Protocol Servers</div>
          <div class="code-box" id="mcpToolsBox">Loading tools...</div>
        </div>
        <div class="card">
          <div class="card-title">Execute MCP Tool</div>
          <div style="display: flex; gap: 10px; margin-bottom: 12px;">
            <input type="text" id="mcpServer" class="chat-input" style="max-width: 160px;" placeholder="Server (e.g. system_info)">
            <input type="text" id="mcpTool" class="chat-input" style="max-width: 160px;" placeholder="Tool (e.g. get_os_info)">
            <button class="btn" onclick="executeMCP()">Run Tool</button>
          </div>
          <div class="code-box" id="mcpResultBox">Tool output will appear here...</div>
        </div>
      </div>

      <!-- 7. EVOLUTION TAB -->
      <div id="tab-evolution" class="tab-content">
        <div class="card">
          <div class="card-title">Self-Evolver Mutation History (Layer 2)</div>
          <div class="code-box" id="evolutionHistoryBox">Loading history...</div>
        </div>
      </div>

    </div>
  </div>

  <script>
    function switchTab(name) {
      document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
      document.querySelectorAll('.nav-btn').forEach(el => el.classList.remove('active'));
      document.getElementById('tab-' + name).classList.add('active');
      event.currentTarget.classList.add('active');
      
      const titles = {
        chat: 'Personal Assistant Chat',
        overview: 'System Overview & Executive Briefing',
        swarm: 'Autonomous Multi-Agent Swarm',
        tasks: 'Tasks & Calendar Management',
        rag: 'Knowledge Base & Document RAG',
        mcp: 'Model Context Protocol (MCP) Tools',
        evolution: 'Layer 2 Self-Evolution History'
      };
      document.getElementById('pageTitle').innerText = titles[name] || 'Command Center';
      
      if (name === 'overview') loadOverview();
      if (name === 'tasks') loadTasksAndCalendar();
      if (name === 'mcp') loadMCP();
      if (name === 'evolution') loadEvolution();
    }

    async function sendMessage() {
      const input = document.getElementById('chatInput');
      const text = input.value.trim();
      if (!text) return;

      const container = document.getElementById('chatMessages');
      container.innerHTML += `<div class="message user">${text}</div>`;
      input.value = '';
      container.scrollTop = container.scrollHeight;

      const loaderId = 'loader-' + Date.now();
      container.innerHTML += `<div class="message assistant" id="${loaderId}">Thinking...</div>`;
      container.scrollTop = container.scrollHeight;

      try {
        const res = await fetch('/api/chat', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({message: text})
        });
        const data = await res.json();
        document.getElementById(loaderId).innerText = data.reply || data.error;
        if (data.evolution && data.evolution.evolved) {
          document.getElementById('pillVersion').innerText = 'Version: v' + data.evolution.version;
        }
      } catch (err) {
        document.getElementById(loaderId).innerText = 'Error: ' + err.message;
      }
      container.scrollTop = container.scrollHeight;
    }

    async function loadOverview() {
      try {
        const [statusRes, briefRes] = await Promise.all([
          fetch('/api/status').then(r => r.json()),
          fetch('/api/briefing').then(r => r.json())
        ]);
        document.getElementById('statGatewayDetails').innerText = statusRes.gateway.active_providers.join(', ');
        document.getElementById('statVersion').innerText = 'v' + statusRes.evolver.version;
        document.getElementById('statEvolver').innerText = statusRes.evolver.summary;
        document.getElementById('statRAGChunks').innerText = statusRes.rag.total_chunks + ' indexed chunks';
        document.getElementById('briefingBox').innerText = briefRes.briefing;
      } catch (e) {
        console.error(e);
      }
    }

    async function loadTasksAndCalendar() {
      try {
        const [tasksRes, calRes] = await Promise.all([
          fetch('/api/tasks').then(r => r.json()),
          fetch('/api/calendar').then(r => r.json())
        ]);
        const tasksHtml = tasksRes.tasks.map(t => `
          <div class="list-item">
            <div>
              <span class="badge badge-${t.priority.toLowerCase()}">${t.priority}</span>
              <span style="margin-left: 8px;">${t.description}</span>
            </div>
            <span style="color: var(--text-muted); font-size: 11px;">${t.status}</span>
          </div>
        `).join('');
        document.getElementById('tasksList').innerHTML = tasksHtml || 'No tasks found.';

        const calHtml = calRes.events.map(e => `
          <div class="list-item">
            <div><strong>${e.title}</strong> (${e.start_time} - ${e.end_time})</div>
            <span style="color: var(--text-muted); font-size: 11px;">${e.day}</span>
          </div>
        `).join('');
        document.getElementById('calendarList').innerHTML = calHtml || 'No events found.';
      } catch (e) {
        console.error(e);
      }
    }

    async function searchRAG() {
      const q = document.getElementById('ragQuery').value.trim();
      if (!q) return;
      document.getElementById('ragResults').innerText = 'Searching knowledge base...';
      const res = await fetch('/api/rag/search?q=' + encodeURIComponent(q));
      const data = await res.json();
      document.getElementById('ragResults').innerText = data.results;
    }

    async function loadMCP() {
      const res = await fetch('/api/mcp/tools');
      const data = await res.json();
      document.getElementById('mcpToolsBox').innerText = data.tools;
    }

    async function executeMCP() {
      const server = document.getElementById('mcpServer').value.trim();
      const tool = document.getElementById('mcpTool').value.trim();
      document.getElementById('mcpResultBox').innerText = 'Executing...';
      const res = await fetch('/api/mcp/execute', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({server_name: server, tool_name: tool})
      });
      const data = await res.json();
      document.getElementById('mcpResultBox').innerText = data.result;
    }

    async function runSwarm() {
      const goal = document.getElementById('swarmGoal').value.trim();
      if (!goal) return;
      document.getElementById('swarmOutput').innerText = 'Running autonomous 3-agent pipeline (Researcher -> Coder -> Reviewer)... This may take 15-20 seconds...';
      try {
        const res = await fetch('/api/swarm/collaborate', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({objective: goal})
        });
        const data = await res.json();
        document.getElementById('swarmOutput').innerText = data.report || data.error;
      } catch (e) {
        document.getElementById('swarmOutput').innerText = 'Error: ' + e.message;
      }
    }

    async function loadEvolution() {
      const res = await fetch('/api/status');
      const data = await res.json();
      document.getElementById('evolutionHistoryBox').innerText = JSON.stringify(data.evolver.history, null, 2);
    }
  </script>
</body>
</html>
"""

async def homepage(request):
    return HTMLResponse(HTML_PAGE)

routes = [
    Route("/", homepage),
    Route("/api/status", api_status),
    Route("/api/chat", api_chat, methods=["POST"]),
    Route("/api/briefing", api_briefing),
    Route("/api/tasks", api_tasks, methods=["GET", "POST"]),
    Route("/api/tasks/complete", api_complete_task, methods=["POST"]),
    Route("/api/calendar", api_calendar, methods=["GET", "POST"]),
    Route("/api/rag/search", api_rag_search),
    Route("/api/rag/index", api_rag_index, methods=["POST"]),
    Route("/api/mcp/tools", api_mcp_tools),
    Route("/api/mcp/execute", api_mcp_execute, methods=["POST"]),
    Route("/api/swarm/collaborate", api_swarm_collaborate, methods=["POST"]),
]

middleware = [
    Middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
]

app = Starlette(debug=True, routes=routes, middleware=middleware)

if __name__ == "__main__":
    import uvicorn
    print("[*] Starting AI Agent Web Dashboard on http://localhost:8000")
    uvicorn.run("web.server:app", host="127.0.0.1", port=8000, reload=False)
