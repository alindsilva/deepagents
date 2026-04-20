from typing import Any
from docker_agent_bridge.utils import interpolate_env_vars

def resolve_mcp_connections(toolsets_config: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Resolve MCP connections from toolsets configuration.

    Args:
        toolsets_config: The toolsets block from an agent configuration.

    Returns:
        A dictionary mapping server names to connection configurations.
    """
    connections = {}
    mcp_counter = 0

    for toolset in toolsets_config:
        if toolset.get("type") != "mcp":
            continue

        server_name = None
        conn_config = {}

        if "ref" in toolset:
            ref = toolset["ref"]
            if ref.startswith("docker:"):
                image = ref.replace("docker:", "")
                server_name = image
                conn_config = {
                    "transport": "stdio",
                    "command": "docker",
                    "args": ["run", "-i", "--rm", image]
                }
        elif "command" in toolset:
            server_name = toolset.get("name")
            conn_config = {
                "transport": "stdio",
                "command": toolset["command"],
                "args": toolset.get("args", [])
            }
        elif "remote" in toolset:
            remote = toolset["remote"]
            server_name = toolset.get("name")
            
            headers = {}
            for k, v in remote.get("headers", {}).items():
                headers[k] = interpolate_env_vars(v)

            transport = "streamable_http" if remote.get("transport_type") == "streamable" else "sse"
            
            conn_config = {
                "transport": transport,
                "url": interpolate_env_vars(remote["url"]),
                "headers": headers
            }

        if conn_config:
            if not server_name:
                server_name = f"mcp_{mcp_counter}"
                mcp_counter += 1
            
            # Preserve the tools allowlist if present
            conn_config["__tools_filter__"] = toolset.get("tools")
            connections[server_name] = conn_config

    return connections
