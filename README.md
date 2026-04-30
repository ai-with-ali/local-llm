# Agentful — Local agentic AI starter for engineers

> A production-ready template for building agentic AI systems with local LLMs —
> no API keys, no cloud costs, everything runs on your own machine.

[![Python](https://img.shields.io/badge/python-3.12%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![uv](https://img.shields.io/badge/package%20manager-uv-purple)](https://github.com/astral-sh/uv)

---

## Overview

**Agentful** is an engineer-facing starter template for building agentic AI
applications backed entirely by local LLMs. It wires together the most important
open protocols and frameworks in the agentic AI ecosystem — **A2A**, **MCP**,
**LangGraph**, and **Chainlit** — into a clean, extensible architecture you can
clone and build on today.

![Agent demo](agent.gif)

**Use Agentful to:**

- Learn how agentic AI systems are structured in practice.
- Bootstrap a new local agent project with best-practice patterns already in place.
- Experiment with A2A multi-agent orchestration and MCP tool serving without
  writing boilerplate.

---

## Stack

| Component | Role |
|---|---|
| [Ollama](https://ollama.com/) | Serves the LLM locally via an OpenAI-compatible HTTP API |
| [Gemma 4 e2b](https://ai.google.dev/gemma/docs/core) | Lightweight quantised model (~2 GB), runs on laptop GPU or CPU |
| [LangGraph](https://github.com/langchain-ai/langgraph) | Agent reasoning loop with persistent memory and checkpointing |
| [A2A SDK](https://github.com/google-deepmind/a2a) | Agent-to-Agent protocol — standardised inter-agent communication |
| [FastMCP](https://github.com/jlowin/fastmcp) | Exposes Python functions as MCP tools over HTTP |
| [langchain-mcp-adapters](https://github.com/langchain-ai/langchain-mcp-adapters) | Discovers and wraps MCP tools for use in LangChain agents |
| [Chainlit](https://chainlit.io/) | Streaming chat web UI with per-session thread management |

---

## Architecture

```mermaid
flowchart LR
    User["💬 Chat UI\nlocalhost:8000"]

    subgraph Orchestrator ["🧭 Orchestrator — picks the right agent"]
        Router["Agent Router\nreads agents.yaml"]
        Sender["<<A2A Client>>\n📡 Sends tasks & receives\nstreamed responses over SSE"]
    end

    subgraph Agent ["🤖 Data Analysis Agent — localhost:10001"]
        Handler["<<A2A Server>>\n📡 Accepts tasks &\nstreams events back"]
        Brain["<<LangGraph Agent>>\n🔁 Reasons step by step\nusing tools & memory"]
        LLM["🧠 Local LLM\ngemma4:e2b · localhost:11434"]
        Tools["<<MCP Tools Server>>\n🔧 add · multiply\nlocalhost:8001"]
    end

    User -- "sends question" --> Router
    Router -- "picks best agent" --> Sender
    Sender -- "A2A: forwards question" --> Handler
    Handler --> Brain
    Brain -- "asks LLM" --> LLM
    LLM -- "streams answer tokens" --> Brain
    Brain -- "MCP: calls a tool" --> Tools
    Tools -- "MCP: returns result" --> Brain
    Brain -- "sends answer" --> Handler
    Handler -- "A2A: streams back" --> Sender
    Sender -- "token by token" --> User
```

### Key design patterns

| Pattern | Where | Why |
|---|---|---|
| **A2A protocol** | `src/a2a/` | Standardised agent-to-agent communication — swap or add agents without touching the orchestrator |
| **MCP tool serving** | `src/mcp/` | Tools are plain Python functions; discovery is automatic |
| **LangGraph reasoning loop** | `src/agents/da_agent/graph.py` | Persistent memory, tool-use loop, and checkpointing out of the box |
| **Token streaming** | `adapter.py` → `executor_base.py` → `client.py` → `app.py` | Each LLM token is forwarded end-to-end via SSE artifact chunks |
| **Declarative agent registry** | `config/agents.yaml` | Add a new agent server without touching any Python |

---

## Prerequisites

Before you begin, make sure you have the following installed and running:

| Requirement | Version / notes |
|---|---|
| Python | 3.12 or later |
| [uv](https://github.com/astral-sh/uv) | Recommended package manager |
| [Ollama](https://ollama.com/download) | Must be running (`ollama serve`) |
| Gemma 4 e2b | Pull with `ollama pull gemma4:e2b` |

---

## Project structure

```
.
├── config/
│   └── agents.yaml                   # Declarative A2A agent registry
├── src/
│   ├── app.py                        # Chainlit UI — session lifecycle and message streaming
│   ├── agents/
│   │   └── da_agent/
│   │       └── graph.py              # LangGraph agent (Ollama LLM + MCP tools + MemorySaver)
│   ├── a2a/
│   │   ├── agents/
│   │   │   └── da_agent/
│   │   │       ├── adapter.py        # LangGraph → A2A stream adapter (token streaming)
│   │   │       ├── card.py           # Agent Card definition
│   │   │       ├── executor.py       # A2A executor wiring
│   │   │       └── __main__.py       # Agent server entrypoint (uvicorn)
│   │   ├── base/
│   │   │   ├── agent_base.py         # BaseA2AAgent ABC
│   │   │   ├── executor_base.py      # BaseAgentExecutor — task lifecycle and token streaming
│   │   │   ├── response_format.py    # AgentStreamChunk TypedDict
│   │   │   └── server_factory.py     # Starlette ASGI app factory
│   │   └── orchestrator/
│   │       ├── client.py             # A2AAgentClient — SSE streaming client
│   │       └── registry.py          # AgentRegistry — discovery and skill-based routing
│   └── mcp/
│       ├── client/
│       │   └── master_mcp_client.py  # MultiServerMCPClient — tool discovery
│       └── server/
│           └── math/
│               └── server.py         # FastMCP server — add() and multiply() tools
├── main.py                           # Chainlit entrypoint
├── chainlit.md                       # Chainlit welcome screen
├── pyproject.toml                    # Project metadata and dependencies
└── .env.example                      # Environment variable template
```

---

## Set up

### 1. Clone the repository

```bash
git clone https://github.com/ai-with-ali/agentful.git
cd agentful
```

### 2. Install dependencies

```bash
uv sync
```

### 3. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` with your settings:

```env
OLLAMA_SERVER_URL=http://localhost:11434
MCP_DataAnalysis_Host=localhost
MCP_DataAnalysis_Port=8001
```

### 4. Start Ollama and pull the model

```bash
ollama serve
ollama pull gemma4:e2b   # first run only
```

---

## Run the application

Three processes must run simultaneously. Open three separate terminals.

**Terminal 1 — MCP tool server**

```bash
uv run python -m src.mcp.server.math.server
```

Runs at `http://localhost:8001` (or whichever port you set in `.env`).

**Terminal 2 — Data Analysis A2A agent**

```bash
uv run python -m src.a2a.agents.da_agent --port 10001
```

Agent Card available at `http://localhost:10001/.well-known/agent-card.json`.

**Terminal 3 — Chainlit web UI**

```bash
uv run chainlit run main.py --port 8000
```

Open [http://localhost:8000](http://localhost:8000) in your browser.

> **VS Code users:** use the **Run & Debug** panel. Select each configuration
> from the dropdown and press `F5`.

---

## How it works

1. **User sends a message** in the Chainlit UI.
2. **`AgentRegistry`** reads `config/agents.yaml`, fetches each agent's Card from
   `/.well-known/agent-card.json`, and routes the query to the best-matching agent
   by skill-tag matching.
3. **`A2AAgentClient`** opens a JSONRPC/SSE stream to the selected A2A agent server.
4. **`BaseAgentExecutor`** runs the LangGraph agent and forwards events upstream:
   - Tool call details (name and arguments) → `TASK_STATE_WORKING` status update
   - Tool results → `TASK_STATE_WORKING` status update
   - LLM tokens → `TaskArtifactUpdateEvent` chunks (streamed immediately)
5. **Chainlit** renders working events as a collapsible step and streams each LLM
   token into the reply message in real time.

---

## Add a new agent

1. Create `src/agents/<your_agent>/graph.py` with your LangGraph graph.
2. Create `src/a2a/agents/<your_agent>/` mirroring the `da_agent` structure:
   `adapter.py`, `card.py`, `executor.py`, `__main__.py`.
3. Add the agent URL to `config/agents.yaml` — no other changes are needed.

---

## Add a new MCP tool

Open `src/mcp/server/math/server.py` and add a decorated function:

```python
@mcp.tool()
def divide(a: float, b: float) -> float:
    """Divide a by b."""
    return a / b
```

Restart the MCP server. The tool is automatically discovered by the agent on
the next startup.

---

## Contributing

1. Fork the repository.
2. Create a feature branch: `git checkout -b feat/your-feature`
3. Commit your changes using [Conventional Commits](https://www.conventionalcommits.org/).
4. Open a pull request against `main`.
