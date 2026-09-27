# Hermit Agent: Autonomous Multi-Layer AI System

An enterprise-grade, autonomous, multi-layered AI agent architecture with **Universal API Routing**, **Self-Evolution**, **Hybrid RAG**, **Model Context Protocol (MCP)**, **Multi-Agent Swarm**, and **Web Scraping / Browser Search**.

---

## 🏛️ System Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                      LAYER 1: PERSONAL ASSISTANT                       │
│  - Executive Chief-of-Staff & Daily Concierge                          │
│  - Persistent Memory Store (Letta/MemGPT pattern: profile & facts)    │
│  - Calendar, Tasks (P1/P2/P3), and Executive Briefing Tools           │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│              LAYER 2: SELF-EVOLVER & UNIVERSAL API GATEWAY             │
│                                                                        │
│  [1] UNIVERSAL API GATEWAY (`gateway/`)                                │
│      • Multi-Provider Routing: OpenRouter, Gemini, Groq, Nebius        │
│      • Zero-Downtime Auto-Failover (handles 402 credits & 429 limits)  │
│                                                                        │
│  [2] SELF-EVOLVER ENGINE (`evolver/`)                                  │
│      • Evolves ONLY on real failure signals (tool errors, explicit     │
│        user corrections, refusals) - never on keyword coincidence      │
│      • Evolved rules persist to disk and reload on every restart       │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│           LAYER 3: MODEL CONTEXT PROTOCOL (MCP) & HYBRID RAG           │
│                                                                        │
│  [1] HYBRID RAG ENGINE (`rag/`)                                        │
│      • Hybrid scoring: local/free embeddings (vLLM/Ollama/Gemini) +    │
│      • keyword term-frequency fallback when no embedder is running     │
│      • Auto-indexes markdown/text docs into `data/knowledge/index.json`│
│                                                                        │
│  [2] MCP CLIENT HUB (`mcp_hub/`)                                       │
│      • REAL MCP protocol: JSON-RPC 2.0 over stdio AND streamable HTTP  │
│      • Live tool discovery via tools/list; servers in `mcp_config.json`│
│      • Ships a zero-dep example server (`mcp_servers/notes_server.py`) │
│      • Built-ins (filesystem, system_info, browser) honestly labeled   │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│             LAYER 4: AUTONOMOUS MULTI-AGENT SWARM (`swarm/`)           │
│  - Researcher Agent: Deep analysis, document citations, fact-checking  │
│  - QA Reviewer: Logic auditing, edge-case analysis, confidence scoring │
│  - Swarm Orchestrator: Autonomous 3-stage collaborative pipelines      │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│        LAYER 5: WEB SCRAPING, BROWSER AUTOMATION & MULTI-MODEL CODER   │
│  - Web Scraper (`tools/browser.py`): Clean text extraction (0 deps)    │
│  - Browser Search: Live DuckDuckGo search without API keys             │
│  - Browser MCP Server: `scrape_url` and `search_web` via MCP           │
│  - Multi-Model Coder (`swarm/coder.py`): Code generation & vision      │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 📂 Project Structure

```
hermit/
├── assistant/                      # Layer 1: Personal Assistant
│   ├── agent.py                    # UniversalGatewayAgent & Antigravity integration
│   ├── memory.py                   # Long-term persistent memory store
│   ├── router.py                   # Intent triage & Swarm delegation
│   └── tools/
│       ├── briefing_tool.py        # Executive daily morning briefing
│       ├── calendar_tool.py        # Schedule & event manager
│       └── tasks_tool.py           # Priority task tracker (P1/P2/P3)
│
├── gateway/                        # Layer 2: Universal API Gateway
│   ├── config.py                   # Provider keys & API endpoints
│   ├── providers.py                # OpenRouter, Gemini & OpenAI-compatible adapters
│   └── router.py                   # Auto-failover & circuit breaking
│
├── evolver/                        # Layer 2: Self-Evolver Engine
│   ├── evaluator.py                # Signal-based failure detection (no keyword false positives)
│   ├── mutator.py                  # Operating-rules mutation engine (LLM + offline fallback)
│   └── engine.py                   # Persistence, versioning & loop guard (`data/learned_skills/`)
│
├── rag/                            # Layer 3: Hybrid RAG Knowledge Base
│   ├── indexer.py                  # Document chunker & indexer
│   ├── retriever.py                # Hybrid keyword + phrase score retrieval
│   └── store.py                    # JSON chunk persistence (`data/knowledge/`)
│
├── mcp_hub/                        # Layer 3: Model Context Protocol (MCP)
│   ├── client.py                   # Real MCP client (stdio + HTTP JSON-RPC) + builtins
│   └── config.py                   # Server configuration loader
│
├── mcp_servers/                    # Example REAL MCP servers (zero deps)
│   └── notes_server.py             # Persistent notes over stdio JSON-RPC
│
├── swarm/                          # Layer 4: Autonomous Multi-Agent Swarm
│   ├── base.py                     # BaseSpecialistAgent class
│   ├── researcher.py               # Deep research & RAG synthesis
│   ├── coder.py                    # Software engineering & architecture
│   ├── reviewer.py                 # QA critique & verification
│   └── orchestrator.py             # 3-stage collaborative workflow coordinator
│
├── web/                            # Modern Web UI & REST API Server
│   └── server.py                   # Starlette async server & command center dashboard
│
├── data/                           # Auto-managed persistent data stores
│   ├── user_memory.json            # Profile & remembered facts
│   ├── calendar_events.json        # Scheduled events
│   ├── tasks.json                  # Active tasks
│   ├── evolution_log.json          # System mutation log & version tracker
│   ├── learned_skills/             # Persisted evolved operating rules (reloaded on start)
│   └── knowledge/index.json        # RAG chunk store
│
├── main.py                         # Interactive CLI runner
├── mcp_config.json                 # MCP server definitions
└── .env                            # Active provider keys & config
```

---

## 🚀 How to Run

### 0. Install dependencies
```powershell
.\.venv\Scripts\python -m pip install -r requirements.txt
```

### 1. Run the Interactive CLI Assistant
```powershell
.\.venv\Scripts\python main.py
```
From the CLI prompt, you can:
- Ask about your day: *"What does my day look like?"*
- Manage tasks: *"Add a P1 task to review pull requests"*
- Query documentation (RAG): *"Based on docs, how does the API Gateway work?"*
- Run MCP tools: *"What operating system and python version are we on?"*
- Use the real MCP notes server: *"add a note: buy GPU thermal paste"*
- Run Swarm workflows: *"Run swarm workflow: Design an automated alert system"*

---

### 2. Run the Web UI Command Center
```powershell
.\.venv\Scripts\python -m uvicorn web.server:app --port 8001
```
Open **[http://localhost:8001](http://localhost:8001)** (port 8000 stays reserved for the local vLLM server) in your browser for a dark-mode command center with:
- **Interactive Chat**: Live conversation with the 4-layer agent.
- **Executive Overview**: Real-time morning briefing, provider status, and evolver version.
- **Autonomous Swarm Hub**: Trigger 3-stage collaborative pipelines (Researcher &rarr; Coder &rarr; Reviewer) with live progress logging.
- **Tasks & Calendar**: Visual task manager and scheduled events.
- **Knowledge Base (RAG)**: Live chunk search and document queries.
- **MCP Explorer**: Inspect connected servers and execute tools on demand.
- **Self-Evolution**: View all logged mutation history and version increments.

---

## 🔌 MCP servers (real protocol)

`mcp_config.json` declares servers. Two kinds:

```jsonc
{
  "mcpServers": {
    "notes": {                                 // REAL MCP over stdio
      "command": "${PYTHON}",                  // ${PYTHON} = current interpreter
      "args": ["${ROOT}/mcp_servers/notes_server.py"],
      "enabled": true
    },
    "remote": {                                // REAL MCP over streamable HTTP
      "url": "https://example.com/mcp",
      "headers": {"Authorization": "Bearer ..."},
      "enabled": false
    },
    "filesystem": {"type": "builtin", "enabled": true}  // built-in, not MCP
  }
}
```

## 📚 RAG modes

Retrieval is hybrid when an embedding backend is reachable, keyword-only otherwise:

| Backend  | Config | Notes |
|----------|--------|-------|
| vLLM     | `LOCAL_VLLM_URL` + `VLLM_EMBED_MODEL` | local-first |
| Ollama   | `OLLAMA_URL` + `OLLAMA_EMBED_MODEL` (default `nomic-embed-text`) | local-first |
| Gemini   | `GEMINI_API_KEY` + `GEMINI_EMBED_MODEL` | free tier |
| none     | `RAG_EMBED_PROVIDER=none` | force keyword-only |
