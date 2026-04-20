import os
import pytest
from unittest.mock import patch, MagicMock
from textwrap import dedent

from docker_agent_bridge.parser import parse_yaml_config
from docker_agent_bridge.models import resolve_models
from docker_agent_bridge.mcp import resolve_mcp_connections
from docker_agent_bridge.orchestration import build_agent_graph

def test_portfolio_provider_and_model_resolution(monkeypatch):
    monkeypatch.setenv("CLOUDFLARE_ACCOUNT_ID", "acc123")
    monkeypatch.setenv("CLOUDFLARE_GATEWAY_ID", "gw123")
    monkeypatch.setenv("CLOUDFLARE_AI_GATEWAY_TOKEN", "tok123")
    monkeypatch.setenv("GOOGLE_API_KEY", "goog123")

    yaml_content = dedent("""
        providers:
          google-ai-studio:
            api_type: openai_chatcompletions
            base_url: https://gateway.ai.cloudflare.com/v1/${CLOUDFLARE_ACCOUNT_ID}/${CLOUDFLARE_GATEWAY_ID}/compat
            
        models:
          gemini_flash_via_cloudflare:
            provider: google-ai-studio
            model: gemini-3-flash-preview
            temperature: 0.2
            max_tokens: 4000
            headers:
               cf-aig-authorization: "Bearer ${CLOUDFLARE_AI_GATEWAY_TOKEN}"
               x-goog-api-key: ${GOOGLE_API_KEY}
    """)
    config = parse_yaml_config(yaml_content)
    models = resolve_models(config)
    
    assert "gemini_flash_via_cloudflare" in models
    model = models["gemini_flash_via_cloudflare"]
    
    # Assert base_url from provider was used and interpolated
    # Note: For Cloudflare OpenAI-compatible gateways, we now standardized on /compat
    assert model.openai_api_base == "https://gateway.ai.cloudflare.com/v1/acc123/gw123/compat"
    # Assert headers were merged and interpolated
    assert model.default_headers["cf-aig-authorization"] == "Bearer tok123"
    # cf-aig-authorization is preferred for Cloudflare gateways using OpenAI provider
    assert model.openai_api_key.get_secret_value() == "tok123"

def test_portfolio_mcp_resolution(monkeypatch):
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "supa123")

    yaml_content = dedent("""
        agents:
          root:
            toolsets:
              - type: mcp
                remote:
                  url: "http://localhost:8001/mcp"
                  transport_type: "streamable"
                  headers:
                    Authorization: "Bearer ${env.SUPABASE_SERVICE_ROLE_KEY}"
    """)
    
    config = parse_yaml_config(yaml_content)
    connections = resolve_mcp_connections(config["agents"]["root"]["toolsets"])
    
    assert "mcp_0" in connections
    conn = connections["mcp_0"]
    assert conn["transport"] == "streamable_http"
    assert conn["headers"]["Authorization"] == "Bearer supa123"

@pytest.mark.asyncio
@patch("docker_agent_bridge.orchestration.create_deep_agent")
@patch("docker_agent_bridge.orchestration.resolve_models")
@patch("docker_agent_bridge.orchestration.resolve_tools")
async def test_portfolio_agent_orchestration(mock_resolve_tools, mock_resolve_models, mock_create_deep_agent):
    mock_model = MagicMock()
    mock_resolve_models.return_value = {"gemini_flash_via_cloudflare": mock_model}
    mock_resolve_tools.return_value = []
    
    yaml_content = dedent("""
        agents:
          root:
            model: gemini_flash_via_cloudflare
            description: "Portfolio coordinator"
            skills: true
            max_iterations: 15
            num_history_items: 25
            instruction: "You are the master portfolio manager"
    """)
    config = parse_yaml_config(yaml_content)
    await build_agent_graph(config)
    
    assert mock_create_deep_agent.call_count == 1
    args, kwargs = mock_create_deep_agent.call_args
    
    assert kwargs["model"] == mock_model
    # Standard folders don't exist in test environment, falls back to ['./']
    assert kwargs["skills"] == ["./"]

