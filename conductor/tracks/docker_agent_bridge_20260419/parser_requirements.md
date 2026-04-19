# Parser Requirements: Docker Agent to Deep Agents Bridge

This document details the reverse-engineered requirements for the lightweight parser that translates `docker-agent` YAML configuration into `deepagents` runtime objects.

## 1. Supported Configuration Blocks

The parser must handle the following top-level blocks from the `docker-agent` schema:
- `providers`: Custom model provider configurations.
- `models`: Model definitions.
- `agents`: Agent definitions, including sub-agents and toolsets.
- `mcps`: Reusable MCP server definitions.

### Excluded Advanced Features
To maintain a *lightweight* bridge, the following `docker-agent` features are out of scope:
- **RAG (`rag`)**: Deep Agents does not have a native declarative equivalent for multi-strategy RAG; this would require building custom composite tools.
- **Permissions (`permissions`)**: Deep Agents handles HITL (Human In The Loop) approvals differently.
- **Tool Deferral (`defer`)**: Lazy loading of individual tools is not natively mapped.
- **Hooks (`hooks`)**: While Deep Agents CLI supports hooks, translating arbitrary shell-based lifecycle hooks into the Python graph execution is complex and out of scope for the MVP.

## 2. Block-by-Block Parsing Rules

### 2.1 Providers (`providers`)
- **Purpose**: Defines custom API gateways (e.g., Cloudflare AI Gateway).
- **Mapping**:
  - `base_url`: Maps to `base_url` in LangChain's model initialization.
  - `headers`: Must be parsed and passed as `default_headers` to the model client.
  - **Environment Variables**: The parser must interpolate `${VAR_NAME}` placeholders in the `headers` values using `os.environ`.

### 2.2 Models (`models`)
- **Purpose**: Defines specific LLMs.
- **Mapping**:
  - `provider` & `model`: Maps directly to LangChain's `init_chat_model("provider:model")` or explicit class instantiation.
  - `temperature`, `max_tokens`: Passed as kwargs to the model.
  - `base_url`, `headers`: Merged with the provider block (if referenced) and passed to the model.
  - `provider_opts`: Passed as additional kwargs (e.g., `model_kwargs`).

### 2.3 Agents (`agents`)
- **Purpose**: Defines the root agent and sub-agents.
- **Mapping**:
  - `model`: Resolves to a model defined in the `models` block.
  - `description`: Passed to `create_deep_agent` as the agent's description.
  - `instruction`: Maps to `system_prompt` in `create_deep_agent`.
  - `max_iterations`: Maps to recursion limits in LangGraph.
  - `num_history_items`: Maps to message history truncation limits.
  - `skills`: If `true`, the bridge should load markdown skills from the local `.agents/skills` or `.claude/skills` directories and inject them as tools or system prompt additions.
  - `sub_agents`: Array of string references to other agents defined in the `agents` block. The parser must instantiate these first, convert them using `.as_tool()`, and pass them to the parent agent's `tools` list.
  - `toolsets`: See section 2.4.

### 2.4 Toolsets (`toolsets`)
- **Purpose**: Assigns capabilities to agents.
- **Mapping Rules**:
  - `type: filesystem`: Maps to Deep Agents' `read_file`, `write_file`, `ls`, `grep`, `glob`.
  - `type: todo`: Maps to Deep Agents' `write_todos`.
  - `type: shell`: Maps to Deep Agents' `execute` (shell command tool).
  - `type: think`: Can map to a custom reasoning tool or be ignored if the model natively supports reasoning.
  - `type: script`: Custom CLI wrappers. The parser should convert the `shell` command templates into `langchain_core.tools.StructuredTool` objects that execute the `cmd` using `subprocess.run`.
  - `type: mcp`:
    - If `remote` is provided (e.g., `url`, `transport_type: streamable`, `headers`): Maps to `langchain_mcp_adapters` using `StreamableHttpConnection`. Environment variables in headers must be interpolated.
    - If `ref` starts with `docker:`: Extracts the image name and maps to `StdioConnection` executing `docker run -i --rm <image>`.
    - If `command` and `args` are provided: Maps directly to `StdioConnection`.

## 3. Initialization Order
1. Parse `providers` and resolve env vars.
2. Parse `models` and instantiate LangChain ChatModels.
3. Parse `mcps` and establish MCP client connections.
4. Topologically sort `agents` based on `sub_agents` dependencies.
5. Build sub-agents and convert to tools.
6. Build root agent and compile the LangGraph execution graph.