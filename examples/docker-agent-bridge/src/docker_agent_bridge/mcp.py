from typing import Any, Sequence
from langchain_core.tools import BaseTool
from docker_agent_bridge.utils import interpolate_env_vars

def resolve_mcp_connections(toolsets_config: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Resolve MCP connections from toolsets configuration.

    Args:
        toolsets_config: The toolsets block from an agent configuration.

    Returns:
        A mapping of server names to MCP connection configurations.
    """
    connections = {}
    mcp_counter = 0

    for toolset in toolsets_config:
        if toolset.get("type") != "mcp":
            continue

        conn_config = None
        server_name = None

        # 1. Handle ref-based MCP (e.g. docker:context7)
        if "ref" in toolset:
            ref = toolset["ref"]
            if ref.startswith("docker:"):
                server_name = ref[7:]
                conn_config = {
                    "transport": "stdio",
                    "command": "docker",
                    "args": ["run", "-i", "--rm", ref[7:]]
                }

        # 2. Handle command-based MCP (stdio)
        elif "command" in toolset:
            server_name = toolset.get("name")
            conn_config = {
                "transport": "stdio",
                "command": toolset["command"],
                "args": toolset.get("args", []),
                "env": {k: interpolate_env_vars(v) for k, v in toolset.get("env", {}).items()}
            }

        # 3. Handle remote/streamable MCP (SSE/HTTP)
        elif "remote" in toolset:
            remote = toolset["remote"]
            server_name = toolset.get("name")
            # Default to streamable_http for remote endpoints
            transport = remote.get("transport_type", "streamable")
            if transport == "streamable":
                transport = "streamable_http"
            
            conn_config = {
                "transport": transport,
                "url": interpolate_env_vars(remote["url"]),
                "headers": {k: interpolate_env_vars(v) for k, v in remote.get("headers", {}).items()}
            }

        if conn_config:
            if not server_name:
                server_name = f"mcp_{mcp_counter}"
                mcp_counter += 1
            
            # Internal tracking for tool allowlists
            conn_config["__tools_filter__"] = toolset.get("tools")
            connections[server_name] = conn_config

    return connections

class ScopedMCPClient:
    """Helper that provides a filtered view of tools from a shared MultiServerMCPClient."""
    
    def __init__(self, mcp_tools: Sequence[BaseTool]):
        self._all_tools = mcp_tools

    def get_tools_for_agent(self, toolsets_config: list[dict[str, Any]]) -> list[BaseTool]:
        """Filter the shared tools list based on the agent's toolset allowlists.
        
        If an MCP toolset has a 'tools' list, only tools from that server with matching
        names are returned. If no 'tools' list is provided, all tools from that 
        server are included.
        """
        agent_mcp_configs = resolve_mcp_connections(toolsets_config)
        if not agent_mcp_configs:
            return []

        filtered_tools = []
        for server_name, conn_config in agent_mcp_configs.items():
            allowlist = conn_config.get("__tools_filter__")
            
            # Find tools belonging to this specific server
            server_tools = [
                t for t in self._all_tools 
                if t.name.startswith(f"{server_name}:") 
                or any(server_name in str(getattr(t, "metadata", {})) for _ in [0])
            ]
            
            # Fallback for flattened name matching
            if not server_tools and allowlist:
                server_tools = [t for t in self._all_tools if t.name in allowlist]
            elif not server_tools and not allowlist:
                # Default to giving all tools if we can't attribute them to a specific server
                # and there's no restriction.
                server_tools = list(self._all_tools)

            if allowlist:
                # Apply the allowlist
                filtered = [
                    t for t in server_tools 
                    if t.name in allowlist or (":" in t.name and t.name.split(":", 1)[1] in allowlist)
                ]
                filtered_tools.extend(filtered)
            else:
                filtered_tools.extend(server_tools)

        # De-duplicate
        seen = set()
        unique = []
        for t in filtered_tools:
            if t.name not in seen:
                unique.append(t)
                seen.add(t.name)
        return unique
