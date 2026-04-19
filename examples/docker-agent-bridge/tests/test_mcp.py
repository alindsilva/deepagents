import os
import pytest
from textwrap import dedent

from docker_agent_bridge.parser import parse_yaml_config
from docker_agent_bridge.mcp import resolve_mcp_connections

def test_resolve_mcp_docker_ref():
    yaml_content = dedent("""
        agents:
          root:
            toolsets:
              - type: mcp
                ref: "docker:context7"
    """)
    config = parse_yaml_config(yaml_content)
    connections = resolve_mcp_connections(config["agents"]["root"]["toolsets"])
    
    assert "context7" in connections
    conn = connections["context7"]
    assert conn["transport"] == "stdio"
    assert conn["command"] == "docker"
    assert "run" in conn["args"]
    assert "context7" in conn["args"]

def test_resolve_mcp_stdio_command():
    yaml_content = dedent("""
        agents:
          root:
            toolsets:
              - type: mcp
                command: "uvx"
                args: ["yfmcp"]
    """)
    config = parse_yaml_config(yaml_content)
    connections = resolve_mcp_connections(config["agents"]["root"]["toolsets"])
    
    assert "mcp_0" in connections  # Default name if none provided
    conn = connections["mcp_0"]
    assert conn["transport"] == "stdio"
    assert conn["command"] == "uvx"
    assert conn["args"] == ["yfmcp"]

def test_resolve_mcp_remote_streamable(monkeypatch):
    monkeypatch.setenv("SUPABASE_KEY", "test-key")
    
    yaml_content = dedent("""
        agents:
          root:
            toolsets:
              - type: mcp
                remote:
                  url: "http://localhost:8001/mcp"
                  transport_type: "streamable"
                  headers:
                    Authorization: "Bearer ${SUPABASE_KEY}"
    """)
    config = parse_yaml_config(yaml_content)
    connections = resolve_mcp_connections(config["agents"]["root"]["toolsets"])
    
    assert "mcp_0" in connections
    conn = connections["mcp_0"]
    assert conn["transport"] == "streamable_http"
    assert conn["url"] == "http://localhost:8001/mcp"
    assert conn["headers"]["Authorization"] == "Bearer test-key"

def test_resolve_mcp_complex_headers(monkeypatch):
    monkeypatch.setenv("CF_CLIENT_ID", "id123")
    monkeypatch.setenv("CF_CLIENT_SECRET", "sec123")
    
    yaml_content = dedent("""
        agents:
          trader:
            toolsets:
              - type: mcp
                remote:
                  url: "https://api.casadsilva.com/mcp"
                  transport_type: "streamable"
                  headers:
                    CF-Access-Client-Id: "${env.CF_CLIENT_ID}"
                    CF-Access-Client-Secret: "${env.CF_CLIENT_SECRET}"
    """)
    config = parse_yaml_config(yaml_content)
    connections = resolve_mcp_connections(config["agents"]["trader"]["toolsets"])
    
    conn = connections["mcp_0"]
    assert conn["headers"]["CF-Access-Client-Id"] == "id123"
    assert conn["headers"]["CF-Access-Client-Secret"] == "sec123"

def test_resolve_mcp_skip_non_mcp():
    toolsets = [{"type": "filesystem"}]
    connections = resolve_mcp_connections(toolsets)
    assert connections == {}
