from typing import Any
from deepagents.graph import create_deep_agent
from deepagents.middleware.subagents import CompiledSubAgent
from deepagents.middleware.summarization import SummarizationMiddleware
from deepagents.backends import StateBackend
from docker_agent_bridge.models import resolve_models
from docker_agent_bridge.tools import resolve_tools

async def build_agent_graph(config: dict[str, Any]) -> Any:
    """Build the agent LangGraph from docker-agent YAML configuration.

    Args:
        config: The parsed YAML configuration.

    Returns:
        The compiled root agent graph.
    """
    models = resolve_models(config)
    agents_config = config.get("agents", {})

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
            
            # Wrap as CompiledSubAgent for deepagents middleware
            subagents_specs.append({
                "name": sub_name,
                "description": sub_config.get("description", ""),
                "runnable": sub_graph
            })

        # 2. Resolve tools (non-subagent tools)
        tools = await resolve_tools(agent_data.get("toolsets", []))
        
        # 3. Resolve model
        model_name = agent_data.get("model")
        model = models.get(model_name)
        if isinstance(model, Exception):
            raise RuntimeError(f"Failed to initialize model '{model_name}' for agent '{name}': {model}")
        if not model:
            raise ValueError(f"Model '{model_name}' not found for agent '{name}'")

        # 4. Resolve middleware
        # Note: create_deep_agent adds standard middleware by default.
        num_history = agent_data.get("num_history_items")
        
        # 5. Create the Deep Agent
        skills_paths = ["./skills/"] if agent_data.get("skills") is True else None

        agent = create_deep_agent(
            model=model,
            system_prompt=agent_data.get("instruction"),
            tools=tools,
            subagents=subagents_specs,
            skills=skills_paths,
            middleware=None 
        )

        instantiated_agents[name] = agent
        return agent

    # The entry point is always the 'root' agent
    return await get_agent("root")
