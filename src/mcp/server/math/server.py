import os

from dotenv import load_dotenv
from fastmcp import FastMCP

load_dotenv()

mcp = FastMCP(
    name="DataAnalysis",
    instructions="Provides tools for analyzing numerical datasets. Start with get_summary() for an overview.",
)


@mcp.tool()
def add(a: float, b: float) -> float:
    """Add two numbers."""
    return a + b


@mcp.tool()
def multiply(a: float, b: float) -> float:
    """Multiply two numbers."""
    return a * b


if __name__ == "__main__":
    mcp.run(
        transport="http",
        host=os.getenv("MCP_DataAnalysis_Host"),
        port=int(os.getenv("MCP_DataAnalysis_Port")),
    )
