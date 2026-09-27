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
│      • Continuous turn evaluation, issue diagnosis, and mutation       │
│      • Versioned Evolution Log (`data/evolution_log.json`)             │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│           LAYER 3: MODEL CONTEXT PROTOCOL (MCP) & HYBRID RAG           │
│                                                                        │
│  [1] HYBRID RAG ENGINE (`rag/`)                                        │
│      • Semantic chunking with term-frequency & exact phrase boost      │
│      • Auto-indexes markdown/text docs into `data/knowledge/index.json`│
│                                                                        │
│  [2] MCP CLIENT HUB (`mcp_hub/`)                                       │
│      • Dynamic tool discovery and execution via `mcp_config.json`      │
│      • Connected servers: `filesystem` and `system_info`               │
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
rapo/
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
│   ├── evaluator.py                # Turn evaluator & issue scoring
│   ├── mutator.py                  # Prompt mutation engine
│   └── engine.py                   # Version history tracker
│
├── rag/                            # Layer 3: Hybrid RAG Knowledge Base
│   ├── indexer.py                  # Document chunker & indexer
│   ├── retriever.py                # Hybrid keyword + phrase score retrieval
│   └── store.py                    # JSON chunk persistence (`data/knowledge/`)
│
├── mcp_hub/                        # Layer 3: Model Context Protocol (MCP)
│   ├── client.py                   # Dynamic tool dispatcher (`filesystem`, `system_info`)
│   └── config.py                   # Server configuration loader
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
│   └── knowledge/index.json        # RAG chunk store
│
├── main.py                         # Interactive CLI runner
├── mcp_config.json                 # MCP server definitions
└── .env                            # Active provider keys & config
```

---

## 🚀 How to Run

### 1. Run the Interactive CLI Assistant
```powershell
.\.venv\Scripts\python main.py
```
From the CLI prompt, you can:
- Ask about your day: *"What does my day look like?"*
- Manage tasks: *"Add a P1 task to review pull requests"*
- Query documentation (RAG): *"Based on docs, how does the API Gateway work?"*
- Run MCP tools: *"What operating system and python version are we on?"*
- Run Swarm workflows: *"Run swarm workflow: Design an automated alert system"*

---

### 2. Run the Web UI Command Center
```powershell
.\.venv\Scripts\python -m uvicorn web.server:app --port 8000
```
Open **[http://localhost:8000](http://localhost:8000)** in your browser for a dark-mode command center with:
- **Interactive Chat**: Live conversation with the 4-layer agent.
- **Executive Overview**: Real-time morning briefing, provider status, and evolver version.
- **Autonomous Swarm Hub**: Trigger 3-stage collaborative pipelines (Researcher &rarr; Coder &rarr; Reviewer) with live progress logging.
- **Tasks & Calendar**: Visual task manager and scheduled events.
- **Knowledge Base (RAG)**: Live chunk search and document queries.
- **MCP Explorer**: Inspect connected servers and execute tools on demand.
- **Self-Evolution**: View all logged mutation history and version increments.
