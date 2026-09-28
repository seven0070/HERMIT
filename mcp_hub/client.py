"""Model Context Protocol (MCP) Client Hub.

Two kinds of servers, both declared in mcp_config.json:

1. REAL MCP servers ("command" present): spawned as subprocesses and spoken to
   over stdio with newline-delimited JSON-RPC 2.0 (initialize ->
   notifications/initialized -> tools/list / tools/call). Tool lists are
   discovered from the server itself, never declared statically.
2. Built-in servers ("type": "builtin"): zero-dependency local implementations
   shipped with Hermit. These are honestly labeled as built-ins, not real MCP.

Unknown servers and unknown tools always return errors - never fake success.
"""

import json
import os
import platform
import queue
import subprocess
import httpx
import sys
import threading
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

from mcp_hub.config import load_mcp_config

MCP_PROTOCOL_VERSION = "2024-11-05"
REPO_ROOT = Path(__file__).resolve().parent.parent

class MCPError(Exception):
    pass

class MCPStdioServer:
    """Connection to a real MCP server over stdio (JSON-RPC 2.0, NDJSON)."""

    def __init__(self, name: str, command: str, args: Optional[List[str]] = None, env: Optional[Dict[str, str]] = None):
        self.name = name
        self.command = command
        self.args = args or []
        self.extra_env = env or {}
        self.proc: Optional[subprocess.Popen] = None
        self._responses: "queue.Queue[dict]" = queue.Queue()
        self._next_id = 0
        self._lock = threading.Lock()

    def _resolve(self, value: str) -> str:
        return value.replace("${PYTHON}", sys.executable).replace("${ROOT}", str(REPO_ROOT))

    def start(self, timeout: float = 10.0):
        if self.proc and self.proc.poll() is None:
            return
        cmd = [self._resolve(self.command)] + [self._resolve(a) for a in self.args]
        env = dict(os.environ)
        env.update(self.extra_env)
        self.proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            bufsize=1,
            env=env,
            cwd=str(REPO_ROOT),
        )
        threading.Thread(target=self._read_loop, daemon=True).start()
        # MCP handshake
        self._rpc("initialize", {
            "protocolVersion": MCP_PROTOCOL_VERSION,
            "capabilities": {},
            "clientInfo": {"name": "hermit-agent", "version": "1.0.0"},
        }, timeout=timeout)
        self._notify("notifications/initialized")

    def _read_loop(self):
        assert self.proc and self.proc.stdout
        for line in self.proc.stdout:
            line = line.strip()
            if not line:
                continue
            try:
                self._responses.put(json.loads(line))
            except json.JSONDecodeError:
                continue  # non-JSON noise on stdout is ignored

    def _notify(self, method: str, params: Optional[dict] = None):
        assert self.proc and self.proc.stdin
        self.proc.stdin.write(json.dumps({"jsonrpc": "2.0", "method": method, "params": params or {}}) + "\n")
        self.proc.stdin.flush()

    def _rpc(self, method: str, params: Optional[dict] = None, timeout: float = 30.0) -> Any:
        with self._lock:
            self.start_if_needed()
            self._next_id += 1
            rid = self._next_id
            assert self.proc and self.proc.stdin
            self.proc.stdin.write(json.dumps({
                "jsonrpc": "2.0", "id": rid, "method": method, "params": params or {}
            }) + "\n")
            self.proc.stdin.flush()
            deadline = time.time() + timeout
            while True:
                remaining = deadline - time.time()
                if remaining <= 0:
                    raise MCPError(f"Timeout waiting for '{method}' from MCP server '{self.name}'")
                try:
                    msg = self._responses.get(timeout=remaining)
                except queue.Empty:
                    raise MCPError(f"Timeout waiting for '{method}' from MCP server '{self.name}'")
                if msg.get("id") != rid:
                    continue  # server notification or stale message
                if "error" in msg:
                    err = msg["error"]
                    raise MCPError(f"MCP server '{self.name}' error on '{method}': {err.get('message', err)}")
                return msg.get("result")

    def start_if_needed(self):
        if not (self.proc and self.proc.poll() is None):
            self.proc = None
            self.start()

    def list_tools(self) -> List[Dict[str, Any]]:
        result = self._rpc("tools/list")
        return result.get("tools", [])

    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        result = self._rpc("tools/call", {"name": tool_name, "arguments": arguments})
        if result.get("isError"):
            parts = [c.get("text", "") for c in result.get("content", []) if c.get("type") == "text"]
            raise MCPError(f"Tool '{tool_name}' on '{self.name}' failed: {' '.join(parts)}")
        parts = [c.get("text", "") for c in result.get("content", []) if c.get("type") == "text"]
        return "\n".join(parts) if parts else json.dumps(result)

    def shutdown(self):
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()

class MCPHttpServer:
    """Connection to a real MCP server over streamable HTTP (JSON-RPC 2.0).

    Handles both application/json and text/event-stream responses and carries
    the Mcp-Session-Id header after initialize, per the MCP HTTP transport.
    """

    def __init__(self, name: str, url: str, headers: Optional[Dict[str, str]] = None):
        self.name = name
        self.url = url
        self.headers = headers or {}
        self.session_id: Optional[str] = None
        self._next_id = 0
        self._initialized = False

    def start_if_needed(self):
        if not self._initialized:
            self._rpc("initialize", {
                "protocolVersion": MCP_PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {"name": "hermit-agent", "version": "1.0.0"},
            })
            self._post({"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}}, expect_reply=False)
            self._initialized = True

    def _post(self, payload: dict, expect_reply: bool = True) -> Any:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            **self.headers,
        }
        if self.session_id:
            headers["Mcp-Session-Id"] = self.session_id
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(self.url, json=payload, headers=headers)
            sid = resp.headers.get("mcp-session-id")
            if sid:
                self.session_id = sid
            resp.raise_for_status()
            if not expect_reply or resp.status_code == 202:
                return None
            ctype = resp.headers.get("content-type", "")
            if "text/event-stream" in ctype:
                for line in resp.text.splitlines():
                    if line.startswith("data:"):
                        data = line[5:].strip()
                        if data:
                            return json.loads(data)
                raise MCPError(f"MCP server '{self.name}' returned an empty event stream")
            return resp.json()

    def _rpc(self, method: str, params: Optional[dict] = None) -> Any:
        self._next_id += 1
        rid = self._next_id
        msg = self._post({"jsonrpc": "2.0", "id": rid, "method": method, "params": params or {}})
        if msg is None:
            raise MCPError(f"No reply for '{method}' from MCP server '{self.name}'")
        if "error" in msg:
            err = msg["error"]
            raise MCPError(f"MCP server '{self.name}' error on '{method}': {err.get('message', err)}")
        return msg.get("result")

    def list_tools(self) -> List[Dict[str, Any]]:
        result = self._rpc("tools/list")
        return result.get("tools", [])

    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        result = self._rpc("tools/call", {"name": tool_name, "arguments": arguments})
        if result.get("isError"):
            parts = [c.get("text", "") for c in result.get("content", []) if c.get("type") == "text"]
            raise MCPError(f"Tool '{tool_name}' on '{self.name}' failed: {' '.join(parts)}")
        parts = [c.get("text", "") for c in result.get("content", []) if c.get("type") == "text"]
        return "\n".join(parts) if parts else json.dumps(result)

    def shutdown(self):
        pass  # stateless HTTP; nothing to tear down


# ---------------------------------------------------------------------------
# Built-in (non-MCP) server implementations - zero-dependency, clearly labeled.
# ---------------------------------------------------------------------------

def _builtin_system_info(tool_name: str, arguments: Dict[str, Any]) -> str:
    if tool_name == "get_os_info":
        return (
            f"OS: {platform.system()} {platform.release()} ({platform.version()})\n"
            f"Architecture: {platform.machine()}\n"
            f"Processor: {platform.processor()}"
        )
    if tool_name == "get_python_env":
        return (
            f"Python Version: {sys.version}\n"
            f"Executable: {sys.executable}\n"
            f"CWD: {os.getcwd()}"
        )
    raise MCPError(f"Tool '{tool_name}' not found on built-in server 'system_info'. Available: get_os_info, get_python_env")

# The built-in filesystem server is sandboxed: paths must stay under
# MCP_FS_ROOT (default: the repo root). Anything else - absolute paths,
# ".." escapes, sensitive files - is denied. This matters because the web
# API exposes tool execution on localhost.
REPO_ROOT = Path(__file__).resolve().parent.parent
FS_ROOT = Path(os.environ.get("MCP_FS_ROOT", str(REPO_ROOT))).resolve()
SENSITIVE_FILE_NAMES = {".env"}

def _resolve_in_sandbox(raw_path: str) -> Path:
    p = Path(raw_path)
    if not p.is_absolute():
        p = FS_ROOT / p
    resolved = p.resolve()
    if resolved != FS_ROOT and FS_ROOT not in resolved.parents:
        raise MCPError(f"Access denied: '{raw_path}' is outside the filesystem sandbox ({FS_ROOT}).")
    if resolved.name in SENSITIVE_FILE_NAMES:
        raise MCPError(f"Access denied: '{resolved.name}' is a sensitive file and not readable via MCP tools.")
    return resolved

def _builtin_filesystem(tool_name: str, arguments: Dict[str, Any]) -> str:
    if tool_name == "list_directory":
        dir_path = arguments.get("path", ".")
        try:
            p = _resolve_in_sandbox(dir_path)
        except MCPError as e:
            return f"Error: {e}"
        if not p.exists() or not p.is_dir():
            return f"Directory not found: {dir_path}"
        entries = [f"{'[DIR] ' if e.is_dir() else '[FILE]'} {e.name}" for e in p.iterdir()]
        return f"Contents of '{dir_path}':\n" + "\n".join(entries[:25])
    if tool_name == "read_file":
        file_path = arguments.get("path")
        if not file_path:
            return "Error: 'path' argument is required for read_file."
        try:
            p = _resolve_in_sandbox(file_path)
        except MCPError as e:
            return f"Error: {e}"
        if not p.exists() or not p.is_file():
            return f"File not found: {file_path}"
        with open(p, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read(2000)
        return f"--- Contents of {file_path} (first 2000 chars) ---\n{content}"
    raise MCPError(f"Tool '{tool_name}' not found on built-in server 'filesystem'. Available: list_directory, read_file")

def _builtin_browser(tool_name: str, arguments: Dict[str, Any]) -> str:
    from tools.browser import scrape_url, search_web
    if tool_name == "scrape_url":
        return scrape_url(arguments.get("url", ""))
    if tool_name == "search_web":
        return search_web(arguments.get("query", ""))
    raise MCPError(f"Tool '{tool_name}' not found on built-in server 'browser'. Available: scrape_url, search_web")

BUILTIN_SERVERS = {
    "system_info": _builtin_system_info,
    "filesystem": _builtin_filesystem,
    "browser": _builtin_browser,
}

BUILTIN_TOOL_LISTS = {
    "system_info": ["get_os_info", "get_python_env"],
    "filesystem": ["list_directory", "read_file"],
    "browser": ["scrape_url", "search_web"],
}

class MCPClientHub:
    """Manages real MCP stdio servers and labeled built-in servers."""

    def __init__(self):
        self._connections: Dict[str, MCPStdioServer] = {}

    def _server_entry(self, server_name: str) -> Dict[str, Any]:
        servers = load_mcp_config().get("mcpServers", {})
        if server_name not in servers:
            known = ", ".join(sorted(servers)) or "(none configured)"
            raise MCPError(f"MCP server '{server_name}' is not registered in mcp_config.json. Registered: {known}")
        entry = servers[server_name]
        if not entry.get("enabled", True):
            raise MCPError(f"MCP server '{server_name}' is disabled in mcp_config.json.")
        return entry

    def _get_connection(self, server_name: str, entry: Dict[str, Any]) -> MCPStdioServer:
        conn = self._connections.get(server_name)
        if conn is None:
            if entry.get("command"):
                conn = MCPStdioServer(
                    name=server_name,
                    command=entry["command"],
                    args=entry.get("args", []),
                    env=entry.get("env"),
                )
            else:
                conn = MCPHttpServer(
                    name=server_name,
                    url=entry["url"],
                    headers=entry.get("headers"),
                )
            self._connections[server_name] = conn
        conn.start_if_needed()
        return conn

    def list_tools(self) -> str:
        """Lists tools across all enabled servers. Real servers are queried live."""
        servers = load_mcp_config().get("mcpServers", {})
        output = ["=== MCP Servers & Tools ==="]
        for name, details in servers.items():
            if not details.get("enabled", True):
                continue
            desc = details.get("description", "No description")
            if details.get("command") or details.get("url"):
                transport = "stdio" if details.get("command") else "http"
                output.append(f"* [{name}] (real MCP, {transport}) - {desc}")
                try:
                    conn = self._get_connection(name, details)
                    tools = conn.list_tools()
                    for t in tools:
                        output.append(f"   - {t.get('name')}: {t.get('description', '')}")
                except Exception as e:
                    output.append(f"   [connection error: {e}]")
            else:
                output.append(f"* [{name}] (built-in, not MCP) - {desc}")
                tools = BUILTIN_TOOL_LISTS.get(name, details.get("tools", []))
                output.append(f"   Tools: {', '.join(tools)}")
        return "\n".join(output)

    def execute_tool(self, server_name: str, tool_name: str, arguments: Optional[Dict[str, Any]] = None) -> str:
        """Executes a tool on a target server. Unknown tools/servers are errors, never fake success."""
        arguments = arguments or {}
        try:
            entry = self._server_entry(server_name)
        except MCPError as e:
            return f"Error: {e}"

        try:
            if entry.get("command") or entry.get("url"):
                conn = self._get_connection(server_name, entry)
                return conn.call_tool(tool_name, arguments)
            handler = BUILTIN_SERVERS.get(server_name)
            if handler is None:
                return f"Error: server '{server_name}' has no command and no built-in implementation."
            return handler(tool_name, arguments)
        except MCPError as e:
            return f"Error: {e}"
        except Exception as e:
            return f"Error: {type(e).__name__} while running '{tool_name}' on '{server_name}': {e}"

    def shutdown_all(self):
        for conn in self._connections.values():
            conn.shutdown()
        self._connections.clear()

mcp_hub = MCPClientHub()
