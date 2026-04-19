import pytest
from unittest.mock import patch, MagicMock, mock_open, AsyncMock
from docker_agent_bridge.main import run_bridge

@patch("sys.argv", ["bridge", "config.yaml", "--query", "hello"])
@patch("builtins.open", new_callable=mock_open, read_data="agents: {root: {model: gpt}}")
@patch("docker_agent_bridge.main.parse_yaml_config")
@patch("docker_agent_bridge.main.build_agent_graph")
@patch("docker_agent_bridge.main.input", side_effect=["exit"])
def test_run_bridge_with_query(mock_input, mock_build, mock_parse, mock_file):
    # Mock graph
    mock_graph = MagicMock()
    mock_build.return_value = mock_graph
    mock_graph.ainvoke = AsyncMock(return_value={"messages": [MagicMock(content="hi")]})
    
    run_bridge()
    
    # Verify graph was built and invoked
    mock_parse.assert_called_once()
    mock_build.assert_called_once()
    mock_graph.ainvoke.assert_called_once()

@patch("sys.argv", ["bridge", "config.yaml"])
@patch("sys.stdin.isatty", return_value=False)
def test_run_bridge_no_tty_error(mock_tty):
    with pytest.raises(SystemExit):
        run_bridge()

