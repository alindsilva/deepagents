# Docker Agent to Deep Agents Bridge

This example demonstrates how to build a lightweight mapping layer that parses [Docker Agent](https://github.com/docker/docker-agent) YAML configuration files and dynamically instantiates a [Deep Agents](https://docs.langchain.com/oss/python/deepagents/overview) runtime.

## Overview

The bridge allows you to define complex multi-agent teams using a declarative DSL while leveraging the robust, enterprise-ready LangGraph orchestration provided by Deep Agents.

### Supported Features

- **Multi-Agent Hierarchies**: Supports `root` and `sub_agents` delegation.
- **Provider & Model Mapping**: Handles custom base URLs, headers, and environment variable interpolation (e.g., Cloudflare AI Gateway).
- **Tool Mapping**:
  - `filesystem`: Maps to Deep Agents' native file tools.
  - `shell`: Maps to the `execute` tool.
  - `todo`: Maps to the planning tool.
  - `script`: Dynamically creates custom tools from shell commands.
- **MCP Integration**: Supports `docker:`, `command:`, and `remote:` (streamable/SSE) MCP connection formats.

## Setup

1. **Install Dependencies**:
   ```bash
   uv sync
   ```

2. **Set Environment Variables**:
   Ensure you have your LLM provider API keys set (e.g., `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`).

## Usage

Run the bridge against a YAML configuration file:

```bash
uv run python -m docker_agent_bridge.main team.yaml --query "Research LangGraph and summarize its benefits."
```

Or run interactively:

```bash
uv run python -m docker_agent_bridge.main team.yaml
```

## Running Tests

Execute the test suite with coverage:

```bash
uv run pytest --cov=docker_agent_bridge
```
