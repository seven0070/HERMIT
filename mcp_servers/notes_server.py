"""Example REAL MCP server (stdio, JSON-RPC 2.0, zero dependencies).

A tiny persistent notes server Hermit ships with so the MCP hub has a real
protocol server to talk to out of the box. Implements the MCP subset the hub
needs: initialize, notifications/initialized, tools/list, tools/call.

Run standalone:  python mcp_servers/notes_server.py
"""

import json
import sys
from pathlib import Path

NOTES_FILE = Path(__file__).resolve().parent.parent / "data" / "notes.json"

TOOLS = [
    {
        "name": "add_note",
        "description": "Store a short note persistently.",
        "inputSchema": {
            "type": "object",
            "properties": {"text": {"type": "string", "description": "The note text"}},
            "required": ["text"],
        },
    },
    {
        "name": "list_notes",
        "description": "List all stored notes.",
        "inputSchema": {"type": "object", "properties": {}},
    },
]

def _load_notes():
    try:
        return json.loads(NOTES_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []

def _save_notes(notes):
    NOTES_FILE.parent.mkdir(parents=True, exist_ok=True)
    NOTES_FILE.write_text(json.dumps(notes, indent=2, ensure_ascii=False), encoding="utf-8")

def _text_result(text, is_error=False):
    return {"content": [{"type": "text", "text": text}], "isError": is_error}

def handle(request: dict) -> dict:
    method = request.get("method")
    rid = request.get("id")
    params = request.get("params") or {}

    if method == "initialize":
        return {"jsonrpc": "2.0", "id": rid, "result": {
            "protocolVersion": params.get("protocolVersion", "2024-11-05"),
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "hermit-notes", "version": "1.0.0"},
        }}
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": rid, "result": {"tools": TOOLS}}
    if method == "tools/call":
        name = params.get("name")
        args = params.get("arguments") or {}
        if name == "add_note":
            text = (args.get("text") or "").strip()
            if not text:
                return {"jsonrpc": "2.0", "id": rid, "result": _text_result("Error: 'text' is required.", True)}
            notes = _load_notes()
            notes.append(text)
            _save_notes(notes)
            return {"jsonrpc": "2.0", "id": rid, "result": _text_result(f"Note stored ({len(notes)} total).")}
        if name == "list_notes":
            notes = _load_notes()
            body = "\n".join(f"{i+1}. {n}" for i, n in enumerate(notes)) or "No notes yet."
            return {"jsonrpc": "2.0", "id": rid, "result": _text_result(body)}
        return {"jsonrpc": "2.0", "id": rid, "error": {"code": -32601, "message": f"Unknown tool '{name}'"}}
    return {"jsonrpc": "2.0", "id": rid, "error": {"code": -32601, "message": f"Unknown method '{method}'"}}

def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
        except json.JSONDecodeError:
            continue
        if "id" not in request:
            continue  # notification (e.g. notifications/initialized) - no reply
        response = handle(request)
        sys.stdout.write(json.dumps(response) + "\n")
        sys.stdout.flush()

if __name__ == "__main__":
    main()
