"""Configuration loader for Model Context Protocol (MCP) servers."""

import json
from pathlib import Path

CONFIG_PATH = Path(__file__).resolve().parent.parent / "mcp_config.json"

def load_mcp_config() -> dict:
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"mcpServers": {}}
