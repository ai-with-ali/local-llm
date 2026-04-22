# Local LLM — Building AI Agents for Free with Gemma4 + Ollama using Langchain

This project demonstrates how to build a fully local, cost-free AI agent using:

- **[Ollama](https://ollama.com/)** — runs large language models locally on your machine
- **[Gemma 4 (e4b)](https://ai.google.dev/gemma/docs/core)** — Google's efficient open-weight model that runs on consumer hardware
- **[LangChain](https://github.com/langchain-ai/langgraph)** — agent orchestration framework
- **[FastMCP](https://github.com/jlowin/fastmcp)** — lightweight Model Context Protocol (MCP) server for exposing tools to the agent

No API keys. No cloud costs. Everything runs on your own machine.

---

## What You Will Learn

- How to connect a LangGraph agent to a locally running Ollama model
- How to expose custom Python functions as tools via an MCP server
- How the agent uses those tools to answer questions instead of relying on its parametric knowledge
- How to structure a multi-component AI project cleanly (agent, MCP client, MCP server)

---

## Architecture

```
┌──────────────┐     asks question     ┌─────────────────────┐
│   User CLI   │ ───────────────────   │  Ollama running     │
│  (src/app.py)│                       │  (local LLM)        │
└──────────────┘                       └──────────┬──────────┘
                                                  │  calls tools via MCP
                                                  |
                                       ┌─────────────────────┐
                                       │   MCP Server         │
                                       │ (FastMCP / HTTP)     │
                                       │  - add(a, b)         │
                                       │  - multiply(a, b)    │
                                       └─────────────────────┘
```

The agent (Gemma 4 running in Ollama) decides which MCP tool to call based on the user's question, invokes it, and returns the result — no cloud inference required.

---

## Prerequisites

| Requirement | Notes |
|---|---|
| Python ≥ 3.12 | |
| [Ollama](https://ollama.com/download) installed and running | `ollama serve` |
| Gemma 4 e4b model pulled | `ollama pull gemma4:e4b` |
| [uv](https://github.com/astral-sh/uv) (recommended) or pip | For dependency management |

---

## Setup

**1. Clone the repository**

```bash
git clone https://github.com/ai-with-ali/local-llm.git
cd local-llm
```

**2. Install dependencies**

```bash
uv sync
# or
pip install -e .
```

**3. Configure environment variables**

Create a `.env` file in the project root:

```env
OLLAMA_SERVER_URL=http://localhost:11434
MCP_DataAnalysis_Host=127.0.0.1
MCP_DataAnalysis_Port=8000
```

---

## Running the Project

You need two processes running simultaneously — the MCP server and the agent.

**Terminal 1 — Start the MCP tool server**

```bash
python -m src.mcp.server.math.server
```

**Terminal 2 — Start the agent**

```bash
uv run -m src.app
```

Then type your question at the prompt:

```
Data Analysis Agent ready. Type 'exit' or 'quit' to stop.

You: what is 7 multiplied by 6?
Agent: The result is 42.
```

---

## Project Structure

```
.                         
├── pyproject.toml                   # Dependencies
├── .env                             # Environment config (not committed)
└── src/
    ├── app.py                       # Entry point - CLI loop — sends user input to the agent
    ├── agents/
    │   └── da_agent/
    │       └── graph.py             # Builds the LangGraph agent with Ollama + gemma4:e4b and tools
    └── mcp/
        ├── client/
        │   └── master_mcp_client.py # MultiServerMCPClient — discovers tools from MCP servers
        └── server/
            └── math/
                └── server.py        # FastMCP server exposing add() and multiply() as tools
```

---

## Key Concepts

**Why Ollama?**
Ollama makes it trivial to download and serve open-weight models locally. It exposes a standard OpenAI-compatible HTTP API, so it works seamlessly with LangChain's `ChatOllama` integration.

**Why Gemma 4 e4b?**
The `e4b` (4-bit quantized, ~2 GB) variant of Google's Gemma 4 runs comfortably on a laptop GPU or CPU while still being capable enough for tool-calling tasks.

**Why MCP?**
The Model Context Protocol standardises how agents discover and call external tools. Using FastMCP as the server and `langchain-mcp-adapters` as the client means you can add new tools by writing a plain Python function — no manual schema definitions needed.

**Why LangGraph?**
LangGraph gives the agent a persistent reasoning loop with checkpointing, so it can plan, call tools, observe results, and respond — all within a clean graph-based state machine.
