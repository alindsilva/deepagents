import os
import pytest
from textwrap import dedent

from docker_agent_bridge.parser import parse_yaml_config
from docker_agent_bridge.models import resolve_models

def test_resolve_basic_model():
    yaml_content = dedent("""
        models:
          gpt-4o:
            provider: openai
            model: gpt-4o
            temperature: 0.5
            max_tokens: 1000
    """)
    config = parse_yaml_config(yaml_content)
    models = resolve_models(config)
    
    assert "gpt-4o" in models
    model = models["gpt-4o"]
    
    # Assert initialized properties
    assert model.model_name == "gpt-4o"
    assert model.temperature == 0.5
    assert model.max_tokens == 1000

def test_resolve_model_with_provider_and_env_vars(monkeypatch):
    # Set mock environment variables
    monkeypatch.setenv("CLOUDFLARE_ACCOUNT_ID", "test-account")
    monkeypatch.setenv("CLOUDFLARE_GATEWAY_ID", "test-gateway")
    monkeypatch.setenv("CLOUDFLARE_AI_GATEWAY_TOKEN", "test-token")

    yaml_content = dedent("""
        providers:
          cloudflare:
            base_url: https://gateway.ai.cloudflare.com/v1/${CLOUDFLARE_ACCOUNT_ID}/${CLOUDFLARE_GATEWAY_ID}/anthropic
            headers:
              cf-aig-authorization: "Bearer ${CLOUDFLARE_AI_GATEWAY_TOKEN}"

        models:
          claude-sonnet-cloudflare:
            provider: cloudflare
            model: claude-3-5-sonnet-20240620
            temperature: 0.1
    """)
    config = parse_yaml_config(yaml_content)
    models = resolve_models(config)
    
    assert "claude-sonnet-cloudflare" in models
    model = models["claude-sonnet-cloudflare"]
    
    # Assert provider overrides were applied
    assert model.model == "claude-3-5-sonnet-20240620"
    assert model.temperature == 0.1
    assert model.base_url == "https://gateway.ai.cloudflare.com/v1/test-account/test-gateway/anthropic"
    assert "cf-aig-authorization" in model.default_headers
    assert model.default_headers["cf-aig-authorization"] == "Bearer test-token"

def test_resolve_model_with_inline_base_url():
    yaml_content = dedent("""
        models:
          local-qwen:
            provider: openai
            model: qwen3-coder:30b
            base_url: http://localhost:1234/v1
    """)
    config = parse_yaml_config(yaml_content)
    models = resolve_models(config)
    
    assert "local-qwen" in models
    model = models["local-qwen"]
    assert model.model_name == "qwen3-coder:30b"
    assert model.base_url == "http://localhost:1234/v1"

def test_missing_env_var_raises_error():
    yaml_content = dedent("""
        models:
          test-model:
            provider: openai
            model: test
            headers:
              auth: "Bearer ${MISSING_VAR}"
    """)
    config = parse_yaml_config(yaml_content)
    with pytest.raises(ValueError, match="Environment variable MISSING_VAR not found"):
        resolve_models(config)
