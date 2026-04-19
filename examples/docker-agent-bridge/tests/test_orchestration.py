import pytest
from unittest.mock import patch, MagicMock
from textwrap import dedent

from docker_agent_bridge.parser import parse_yaml_config
from docker_agent_bridge.orchestration import build_agent_graph

@patch("docker_agent_bridge.orchestration.create_deep_agent")
@patch("docker_agent_bridge.orchestration.resolve_models")
def test_build_simple_agent(mock_resolve_models, mock_create_deep_agent):
    # Mock models
    mock_model = MagicMock()
    mock_resolve_models.return_value = {"gpt-4o": mock_model}
    
    yaml_content = dedent("""
        models:
          gpt-4o:
            provider: openai
            model: gpt-4o
        agents:
          root:
            model: gpt-4o
            instruction: "You are a helpful assistant"
            toolsets:
              - type: filesystem
    """)
    config = parse_yaml_config(yaml_content)
    
    # We mock the return value of create_deep_agent
    mock_agent = MagicMock()
    mock_create_deep_agent.return_value = mock_agent
    
    agent = build_agent_graph(config)
    
    assert agent == mock_agent
    
    # Verify create_deep_agent was called with correct parameters
    args, kwargs = mock_create_deep_agent.call_args
    assert kwargs["model"] == mock_model
    assert "You are a helpful assistant" in kwargs["system_prompt"]
    # Check that filesystem tools were resolved (our proxy tools from tools.py)
    tool_names = [t.name for t in kwargs["tools"]]
    assert "read_file" in tool_names

@patch("docker_agent_bridge.orchestration.create_deep_agent")
@patch("docker_agent_bridge.orchestration.resolve_models")
def test_build_agent_hierarchy(mock_resolve_models, mock_create_deep_agent):
    # Mock models
    mock_model = MagicMock()
    mock_resolve_models.return_value = {"default": mock_model}
    
    yaml_content = dedent("""
        models:
          default:
            provider: openai
            model: gpt-4o
        agents:
          root:
            model: default
            description: "Main coordinator"
            instruction: "Coordinate the team"
            sub_agents:
              - researcher
          researcher:
            model: default
            description: "Search specialist"
            instruction: "Find information"
    """)
    config = parse_yaml_config(yaml_content)
    
    # Mock sub-agent and root agent creation
    mock_researcher_agent = MagicMock()
    mock_researcher_agent.as_tool.return_value = MagicMock(name="researcher_tool")
    mock_researcher_agent.as_tool.return_value.name = "researcher"
    
    mock_root_agent = MagicMock()
    
    # Side effect for create_deep_agent to return different mocks
    def side_effect(*args, **kwargs):
        if "Find information" in kwargs["system_prompt"]:
            return mock_researcher_agent
        return mock_root_agent
        
    mock_create_deep_agent.side_effect = side_effect
    
    agent = build_agent_graph(config)
    
    assert agent == mock_root_agent
    
    # Verify that researcher was created first and passed as a tool to root
    # Total calls: 1 for researcher, 1 for root
    assert mock_create_deep_agent.call_count == 2
    
    # Last call was for root
    args, kwargs = mock_create_deep_agent.call_args
    tool_names = [t.name for t in kwargs["tools"]]
    assert "researcher" in tool_names
