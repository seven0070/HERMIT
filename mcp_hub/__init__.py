from mcp_hub.client import mcp_hub, MCPClientHub
from mcp_hub.config import load_mcp_config

def list_mcp_tools() -> str:
    """Lists all available tools across connected Model Context Protocol (MCP) servers."""
    return mcp_hub.list_tools()

def call_mcp_tool(server_name: str, tool_name: str, arguments: dict = None) -> str:
    """Invokes a specific tool on a registered MCP server."""
    return mcp_hub.execute_tool(server_name, tool_name, arguments)

__all__ = [
    "mcp_hub",
    "MCPClientHub",
    "list_mcp_tools",
    "call_mcp_tool",
    "load_mcp_config"
]
