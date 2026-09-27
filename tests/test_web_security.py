"""Web API hardening: CORS is not a wildcard, MCP execute is sandboxed."""
from starlette.testclient import TestClient
from web.server import app

client = TestClient(app)

def test_cors_rejects_foreign_origin():
    r = client.options("/api/status", headers={
        "Origin": "https://evil.example",
        "Access-Control-Request-Method": "GET",
    })
    assert r.headers.get("access-control-allow-origin") != "*"
    assert "evil.example" not in r.headers.get("access-control-allow-origin", "")

def test_cors_allows_localhost():
    r = client.options("/api/status", headers={
        "Origin": "http://localhost:8001",
        "Access-Control-Request-Method": "GET",
    })
    assert r.headers.get("access-control-allow-origin") == "http://localhost:8001"

def test_status_endpoint_ok():
    r = client.get("/api/status")
    assert r.status_code == 200
    assert r.json()["status"] == "healthy"

def test_mcp_execute_cannot_escape_sandbox():
    r = client.post("/api/mcp/execute", json={
        "server_name": "filesystem", "tool_name": "read_file",
        "arguments": {"path": "../../etc/passwd"}})
    assert r.status_code == 200
    assert "Access denied" in r.json()["result"]

def test_mcp_execute_reads_repo_file():
    r = client.post("/api/mcp/execute", json={
        "server_name": "filesystem", "tool_name": "read_file",
        "arguments": {"path": "README.md"}})
    assert "Contents of README.md" in r.json()["result"]
