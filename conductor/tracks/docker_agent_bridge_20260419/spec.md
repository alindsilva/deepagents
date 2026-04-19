# Specification: Build lightweight mapping layer from docker-agent YAML to deepagents

## Overview
Create a new example project inside the `deepagents` repository (`examples/docker-agent-bridge/`) that parses `docker-agent` YAML configuration files and dynamically instantiates `deepagents` objects (agents, tools, sub-agents).

## Functional Requirements
- **YAML Parsing:** Read standard `docker-agent` YAML configurations.
- **Tool Mapping:** Convert `docker-agent` toolsets (`filesystem`, `mcp`, `shell`) into their equivalent `deepagents` tools.
- **MCP Integration:** Dynamically handle MCP server configurations, mapping `docker:` refs to `StdioConnection` wrapped in `langchain-mcp-adapters`'s `MultiServerMCPClient`. Also support custom remote MCP connections via URL/headers for `streamable` setups.
- **Agent Orchestration:** Build LangGraph sub-agents and a root agent utilizing `create_deep_agent`.
- **Execution:** Provide a CLI entry point to run the bridge against a given YAML file.

## Out of Scope
- Building a full CLI replacement for `docker-agent`. This is just an example bridge.