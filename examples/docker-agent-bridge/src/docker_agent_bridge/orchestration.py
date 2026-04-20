import os
from typing import Any, Dict, List, Optional, Sequence
from deepagents.graph import create_deep_agent
from deepagents.backends import StateBackend
from deepagents_cli.configurable_model import ConfigurableModelMiddleware
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_core.tools import BaseTool

from docker_agent_bridge.models import resolve_models
from docker_agent_bridge.tools import resolve_tools
from docker_agent_bridge.mcp import resolve_mcp_connections, ScopedMCPClient

class AgentBuilder:
    """Refined recursive builder for Deep Agent graphs defined in YAML."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.agents_config = config.get("agents", {})
        self.models = resolve_models(config)
        self.instantiated_agents = {}
        self.scoped_mcp_client: Optional[ScopedMCPClient] = None

    async def initialize(self):
        """Perform async initialization like loading shared MCP tools."""
        all_mcp_configs = {}
        for agent_data in self.agents_config.values():
            all_mcp_configs.update(resolve_mcp_connections(agent_data.get("toolsets", [])))
        
        # Clean configs for MultiServerMCPClient
        clean_mcp_configs = {
            name: {k: v for k, v in cfg.items() if k != "__tools_filter__"}
            for name, cfg in all_mcp_configs.items()
        }
        
        if clean_mcp_configs:
            mcp_client = MultiServerMCPClient(clean_mcp_configs)
            mcp_tools = await mcp_client.get_tools()
            self.scoped_mcp_client = ScopedMCPClient(mcp_tools)

    async def build(self, agent_name: str = "root") -> Any:
        """Recursively build the agent graph."""
        if agent_name in self.instantiated_agents:
            return self.instantiated_agents[agent_name]

        data = self.agents_config.get(agent_name)
        if not data:
            raise ValueError(f"Agent '{agent_name}' not found in configuration")

        # 1. Resolve recursive sub-agents
        subagents = []
        for sub_name in data.get("sub_agents", []):
            sub_graph = await self.build(sub_name)
            subagents.append({
                "name": sub_name,
                "description": self.agents_config[sub_name].get("description", ""),
                "runnable": sub_graph
            })

        # 2. Resolve tools (local + filtered MCP)
        tools = await resolve_tools(data.get("toolsets", []))
        if self.scoped_mcp_client:
            tools.extend(self.scoped_mcp_client.get_tools_for_agent(data.get("toolsets", [])))
        
        # De-duplicate tools
        seen = set()
        tools = [t for t in tools if t.name not in seen and not seen.add(t.name)]

        # 3. Resolve Model
        model_key = data.get("model")
        model = self.models.get(model_key)
        if isinstance(model, Exception) or not model:
            raise RuntimeError(f"Invalid model '{model_key}' for agent '{agent_name}'")

        # 4. Resolve Skills and Memory
        skills_paths = self._resolve_skills(data)
        memory_paths = data.get("memory")
        if isinstance(memory_paths, str):
            memory_paths = [memory_paths]

        # 5. Instantiate with CLI Middleware for TUI support
        middleware = [ConfigurableModelMiddleware()] if agent_name == "root" else []

        agent = create_deep_agent(
            model=model,
            system_prompt=data.get("instruction"),
            tools=tools,
            subagents=subagents,
            skills=skills_paths,
            memory=memory_paths,
            middleware=middleware
        )

        self.instantiated_agents[agent_name] = agent
        return agent

    def _resolve_skills(self, data: Dict[str, Any]) -> Optional[List[str]]:
        if data.get("skills") is not True:
            return None
        
        paths = []
        candidates = ["./skills/", "./.agents/skills/", "./.claude/skills/"]
        for c in candidates:
            if os.path.isdir(c):
                paths.append(c)
        return paths or ["./"]

async def build_agent_graph(config: Dict[str, Any]) -> Any:
    """Entry point for building the agent graph using the AgentBuilder."""
    builder = AgentBuilder(config)
    await builder.initialize()
    return await builder.build("root")
