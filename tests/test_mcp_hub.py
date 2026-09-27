"""MCP hub: real stdio round-trip, honest errors, filesystem sandbox."""
import pytest
from mcp_hub import call_mcp_tool, list_mcp_tools
from mcp_hub.client import mcp_hub

def teardown_module():
    mcp_hub.shutdown_all()

def test_stdio_notes_roundtrip():
    out = call_mcp_tool("notes", "add_note", {"text": "pytest note"})
    assert "Error" not in out
    out = call_mcp_tool("notes", "list_notes", {})
    assert "pytest note" in out

def test_unknown_tool_and_server_are_errors():
    assert "Error" in call_mcp_tool("notes", "no_such_tool", {})
    assert "Error" in call_mcp_tool("no_such_server", "x", {})
    assert "Error" in call_mcp_tool("filesystem", "no_such_tool", {})

def test_filesystem_sandbox_allows_repo_files():
    out = call_mcp_tool("filesystem", "read_file", {"path": "README.md"})
    assert "Contents of README.md" in out

def test_filesystem_sandbox_blocks_escape():
    out = call_mcp_tool("filesystem", "read_file", {"path": "../../etc/passwd"})
    assert "Access denied" in out
    out = call_mcp_tool("filesystem", "read_file", {"path": "/etc/passwd"})
    assert "Access denied" in out

def test_filesystem_sandbox_blocks_env():
    out = call_mcp_tool("filesystem", "read_file", {"path": ".env"})
    assert "Access denied" in out

def test_list_tools_mentions_transports():
    out = list_mcp_tools()
    assert "real MCP, stdio" in out
    assert "built-in, not MCP" in out
