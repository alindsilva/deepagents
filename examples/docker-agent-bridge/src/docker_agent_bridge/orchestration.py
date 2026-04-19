from typing import Any
from deepagents.graph import create_deep_agent
from deepagents.middleware.subagents import CompiledSubAgent
from deepagents.middleware.summarization import SummarizationMiddleware
from deepagents.backends import StateBackend
from docker_agent_bridge.models import resolve_models
from docker_agent_bridge.tools import resolve_tools

def build_agent_graph(config: dict[str, Any]) -> Any:
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

    def get_agent(name: str):
        if name in instantiated_agents:
            return instantiated_agents[name]

        agent_data = agents_config.get(name)
        if not agent_data:
            raise ValueError(f"Agent '{name}' not found in configuration")

        # 1. Resolve sub-agents (recursive)
        sub_agent_names = agent_data.get("sub_agents", [])
        subagents_specs = []
        for sub_name in sub_agent_names:
            sub_graph = get_agent(sub_name)
            sub_config = agents_config[sub_name]
            
            # Wrap as CompiledSubAgent for deepagents middleware
            subagents_specs.append(CompiledSubAgent(
                name=sub_name,
                description=sub_config.get("description", ""),
                runnable=sub_graph
            ))

        # 2. Resolve tools (non-subagent tools)
        tools = resolve_tools(agent_data.get("toolsets", []))
        
        # 3. Resolve model
        model_name = agent_data.get("model")
        model = models.get(model_name)

        # 4. Resolve middleware
        middleware = []
        num_history = agent_data.get("num_history_items")
        if num_history:
            # Inject summarization middleware to control history size
            middleware.append(SummarizationMiddleware(
                model=model,
                backend=StateBackend(),
                keep=("messages", num_history)
            ))

        # 5. Create the Deep Agent
        # 'skills' in create_deep_agent expects a list of paths. 
        # If skills: true is in YAML, we'll provide default skill paths.
        skills_paths = ["./skills/"] if agent_data.get("skills") is True else None

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
    return get_agent("root")
