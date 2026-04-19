import pytest
from textwrap import dedent
from unittest.mock import MagicMock

from docker_agent_bridge.parser import parse_yaml_config
from docker_agent_bridge.tools import resolve_tools

def test_resolve_script_tool():
    yaml_content = dedent("""
        agents:
          root:
            toolsets:
              - type: script
                shell:
                  my_custom_tool:
                    cmd: "echo hello $arg1"
                    description: "A custom tool"
                    args:
                      arg1:
                        type: string
                        description: "The argument"
    """)
    config = parse_yaml_config(yaml_content)
    # resolve_tools is now async
    import asyncio
    tools = asyncio.run(resolve_tools(config["agents"]["root"]["toolsets"]))
    
    tool_names = [t.name for t in tools]
    assert "my_custom_tool" in tool_names
    
    custom_tool = next(t for t in tools if t.name == "my_custom_tool")
    assert custom_tool.description == "A custom tool"
    
    # Test execution
    result = custom_tool.invoke({"arg1": "world"})
    assert "hello world" in result

@pytest.mark.asyncio
async def test_resolve_script_tool_error():
    yaml_content = dedent("""
        agents:
          root:
            toolsets:
              - type: script
                shell:
                  error_tool:
                    cmd: "ls non_existent_file_12345"
    """)
    config = parse_yaml_config(yaml_content)
    tools = await resolve_tools(config["agents"]["root"]["toolsets"])
    error_tool = next(t for t in tools if t.name == "error_tool")
    
    result = error_tool.invoke({})
    assert "Error:" in result
