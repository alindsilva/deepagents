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
    
    mcp_client = MultiServerMCPClient(all_mcp_configs) if all_mcp_configs else None
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
        
        # Add shared MCP tools
        # For simplicity in this bridge, we give all shared MCP tools to all agents.
        # production logic would filter based on 'tools:' keys in YAML toolsets.
        tools.extend(mcp_tools)
        
        # 3. Resolve model
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
        # Standard skill locations to search if skills: true
        skills_paths = None
        if agent_data.get("skills") is True:
            skills_paths = []
            for candidate in ["./skills/", "./.agents/skills/", "./.claude/skills/"]:
                if os.path.isdir(candidate):
                    skills_paths.append(candidate)
            
            # Fallback to current directory if no standard folders found
            if not skills_paths:
                skills_paths = ["./"]

        agent = create_deep_agent(
            model=model,
            system_prompt=agent_data.get("instruction"),
            tools=tools,
            subagents=subagents_specs,
            skills=skills_paths,
            middleware=middleware
        )

        instantiated_agents[name] = agent
        return agent

    # The entry point is always the 'root' agent
    return await get_agent("root")
