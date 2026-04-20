import os
from typing import Any
from deepagents.graph import create_deep_agent
from deepagents.middleware.summarization import SummarizationMiddleware
from deepagents.backends import StateBackend
from docker_agent_bridge.models import resolve_models
from docker_agent_bridge.tools import resolve_tools
from docker_agent_bridge.mcp import resolve_mcp_connections
from langchain_mcp_adapters.client import MultiServerMCPClient

async def build_agent_graph(config: dict[str, Any]) -> Any:
    """Build the agent LangGraph from docker-agent YAML configuration.

    Args:
        config: The parsed YAML configuration.

    Returns:
        The compiled root agent graph.
    """
    models = resolve_models(config)
    agents_config = config.get("agents", {})

    # 1. Aggregate all MCP connections for a shared client
    all_mcp_configs = {}
    for agent_data in agents_config.values():
        all_mcp_configs.update(resolve_mcp_connections(agent_data.get("toolsets", [])))
    
    # CRITICAL: Strip internal tracking keys (__tools_filter__) before passing to the client
    clean_mcp_configs = {
        name: {k: v for k, v in cfg.items() if k != "__tools_filter__"}
        for name, cfg in all_mcp_configs.items()
    }
    
    mcp_client = MultiServerMCPClient(clean_mcp_configs) if clean_mcp_configs else None
    mcp_tools = await mcp_client.get_tools() if mcp_client else []

    # Memoize instantiated agents to handle hierarchies
    instantiated_agents = {}

    async def get_agent(name: str):
        if name in instantiated_agents:
            return instantiated_agents[name]

        agent_data = agents_config.get(name)
        if not agent_data:
            raise ValueError(f"Agent '{name}' not found in configuration")

        # 1. Resolve sub-agents (recursive)
        sub_agent_names = agent_data.get("sub_agents", [])
        subagents_specs = []
        for sub_name in sub_agent_names:
            sub_graph = await get_agent(sub_name)
            sub_config = agents_config[sub_name]
            
            # Wrap for deepagents middleware
            subagents_specs.append({
                "name": sub_name,
                "description": sub_config.get("description", ""),
                "runnable": sub_graph
            })

        # 2. Resolve local tools (non-MCP)
        tools = await resolve_tools(agent_data.get("toolsets", []))
        
        # 3. Add filtered MCP tools
        agent_mcp_configs = resolve_mcp_connections(agent_data.get("toolsets", []))
        for server_name, conn_config in agent_mcp_configs.items():
            allowlist = conn_config.get("__tools_filter__")
            
            # Find tools belonging to this specific MCP server
            # langchain-mcp-adapters usually uses names like "server:tool" or just "tool"
            server_tools = [
                t for t in mcp_tools 
                if t.name.startswith(f"{server_name}:") or any(server_name in str(getattr(t, "metadata", {})) for _ in [0])
            ]
            
            # If server_tools is empty (common if MultiServerMCPClient flattened them),
            # we fallback to searching all mcp_tools by name if an allowlist exists.
            if not server_tools and allowlist:
                server_tools = [t for t in mcp_tools if t.name in allowlist]
            elif not server_tools and not allowlist:
                # If no allowlist and server not found, we assume all mcp_tools for now
                # to maintain the "everything" fallback.
                server_tools = mcp_tools

            if allowlist:
                # Filter by name (checking both bare name and prefixed name)
                filtered = [
                    t for t in server_tools 
                    if t.name in allowlist or (":" in t.name and t.name.split(":", 1)[1] in allowlist)
                ]
                tools.extend(filtered)
            else:
                # No allowlist, add all tools from this server
                tools.extend(server_tools)
        
        # Remove duplicates while preserving order
        seen_tools = set()
        unique_tools = []
        for t in tools:
            if t.name not in seen_tools:
                unique_tools.append(t)
                seen_tools.add(t.name)
        tools = unique_tools

        # 4. Resolve model
        model_name = agent_data.get("model")
        model = models.get(model_name)
        if isinstance(model, Exception):
            raise RuntimeError(f"Failed to initialize model '{model_name}' for agent '{name}': {model}")
        if not model:
            raise ValueError(f"Model '{model_name}' not found for agent '{name}'")

        # 4. Resolve middleware
        num_history = agent_data.get("num_history_items")
        
        # Add ConfigurableModelMiddleware to support /model in TUI
        from deepagents_cli.configurable_model import ConfigurableModelMiddleware
        middleware = [ConfigurableModelMiddleware()]

        # 5. Create the Deep Agent
        skills_paths = None
        if agent_data.get("skills") is True:
            skills_paths = []
            for candidate in ["./skills/", "./.agents/skills/", "./.claude/skills/"]:
                if os.path.isdir(candidate):
                    skills_paths.append(candidate)
            
            if not skills_paths:
                skills_paths = ["./"]

        # Support native deepagents memory (AGENTS.md files)
        memory_paths = agent_data.get("memory")
        if isinstance(memory_paths, str):
            memory_paths = [memory_paths]

        agent = create_deep_agent(
            model=model,
            system_prompt=agent_data.get("instruction"),
            tools=tools,
            subagents=subagents_specs,
            skills=skills_paths,
            memory=memory_paths,
            middleware=middleware
        )

        instantiated_agents[name] = agent
        return agent

    # The entry point is always the 'root' agent
    return await get_agent("root")
