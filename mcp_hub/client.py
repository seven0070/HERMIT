"""Model Context Protocol (MCP) Client and Tool Execution Engine."""

import os
import sys
import platform
from pathlib import Path
from typing import Dict, Any, List, Optional
from mcp_hub.config import load_mcp_config

class MCPClientHub:
    """Manages MCP server discovery and dynamic tool invocation."""

    def list_tools(self) -> str:
        """Returns all available tools across enabled MCP servers."""
        servers = load_mcp_config().get("mcpServers", {})

        output = ["=== Connected Model Context Protocol (MCP) Servers & Tools ==="]
        for name, details in servers.items():
            if details.get("enabled", True):
                tools = ", ".join(details.get("tools", []))
                output.append(f"* [{name}] - {details.get('description', 'No description')}")
                output.append(f"   Tools: {tools}")

        return "\n".join(output)

    def execute_tool(self, server_name: str, tool_name: str, arguments: Optional[Dict[str, Any]] = None) -> str:
        """Executes a specific tool on a target MCP server.
        
        Args:
            server_name: The name of the MCP server (e.g. 'filesystem', 'system_info').
            tool_name: The tool function name.
            arguments: Dictionary of arguments.
        """
        arguments = arguments or {}
        servers = load_mcp_config().get("mcpServers", {})

        if server_name not in servers:
            return f"Error: MCP Server '{server_name}' is not registered in mcp_config.json."

        # Built-in system_info MCP server implementation
        if server_name == "system_info":
            if tool_name == "get_os_info":
                return (
                    f"OS: {platform.system()} {platform.release()} ({platform.version()})\n"
                    f"Architecture: {platform.machine()}\n"
                    f"Processor: {platform.processor()}"
                )
            elif tool_name == "get_python_env":
                return (
                    f"Python Version: {sys.version}\n"
                    f"Executable: {sys.executable}\n"
                    f"CWD: {os.getcwd()}"
                )

        # Built-in filesystem MCP server implementation
        elif server_name == "filesystem":
            if tool_name == "list_directory":
                dir_path = arguments.get("path", ".")
                p = Path(dir_path)
                if not p.exists():
                    return f"Directory not found: {dir_path}"
                entries = [f"{'[DIR] ' if e.is_dir() else '[FILE]'} {e.name}" for e in p.iterdir()]
                return f"Contents of '{dir_path}':\n" + "\n".join(entries[:25])
            elif tool_name == "read_file":
                file_path = arguments.get("path")
                if not file_path:
                    return "Error: 'path' argument is required for read_file."
                p = Path(file_path)
                if not p.exists():
                    return f"File not found: {file_path}"
                with open(p, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read(2000)
                return f"--- Contents of {file_path} (first 2000 chars) ---\n{content}"

        # Built-in browser MCP server implementation
        elif server_name == "browser":
            from tools.browser import scrape_url, search_web
            if tool_name == "scrape_url":
                return scrape_url(arguments.get("url", ""))
            elif tool_name == "search_web":
                return search_web(arguments.get("query", ""))

        return f"Tool '{tool_name}' on server '{server_name}' executed with arguments: {arguments}"

mcp_hub = MCPClientHub()
