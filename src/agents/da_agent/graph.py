import os

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_ollama import ChatOllama
from langgraph.checkpoint.memory import MemorySaver

from src.mcp.client.master_mcp_client import mcp_client

load_dotenv()

# Must match the server name registered in the MCP client
_SERVER_NAME = "DataAnalysis"

_SYSTEM_PROMPT = (
    "You are a helpful assistant for analyzing numerical datasets. "
    "Use only the tools available to you to answer questions and perform analyses. "
    "If no suitable tool exists for a request, say I can't perform this action "
    "as I don't have the right tool available."
)


async def create_data_analysis_agent():
    """Create and return a compiled DataAnalysis LangGraph agent."""
    tools = await mcp_client.get_tools(server_name=_SERVER_NAME)

    llm = ChatOllama(
        base_url=os.environ["OLLAMA_SERVER_URL"],
        model="gemma4:e2b",
        temperature=0,
    )

    return create_agent(
        model=llm,
        tools=tools,
        system_prompt=_SYSTEM_PROMPT,
        name=f"{_SERVER_NAME}_agent",
        checkpointer=MemorySaver(),
    )
