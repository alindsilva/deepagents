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
