import pytest
from textwrap import dedent

from docker_agent_bridge.parser import parse_yaml_config

def test_parse_valid_yaml():
    yaml_content = dedent("""
        providers:
          cloudflare:
            base_url: https://gateway.ai.cloudflare.com/v1/test
            
        models:
          gpt-4o:
            provider: openai
            model: gpt-4o

        agents:
          root:
            model: gpt-4o
            description: "A test agent"

        mcps:
          test-mcp:
            ref: "docker:context7"
    """)

    config = parse_yaml_config(yaml_content)

    assert "providers" in config
    assert "models" in config
    assert "agents" in config
    assert "mcps" in config

    assert config["providers"]["cloudflare"]["base_url"] == "https://gateway.ai.cloudflare.com/v1/test"
    assert config["agents"]["root"]["model"] == "gpt-4o"


def test_parse_empty_yaml():
    with pytest.raises(ValueError, match="Configuration is empty or invalid"):
        parse_yaml_config("")


def test_parse_partial_yaml():
    yaml_content = dedent("""
        agents:
          root:
            model: my-model
    """)
    config = parse_yaml_config(yaml_content)
    
    assert "agents" in config
    assert "root" in config["agents"]
    
    # Optional sections should be present as empty dicts or handled gracefully
    assert config.get("models", {}) == {}
