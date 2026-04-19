# Product Guide: Deep Agents

## Core Vision
Deep Agents is the "batteries-included" agent harness built on LangGraph. It provides an opinionated, ready-to-run agent out of the box that developers can customize. It abstracts the complexity of wiring up prompts, tools, and context management, offering both a powerful Python SDK and an interactive, terminal-based coding assistant.

## Target Audience
- **Developers:** Building bespoke AI agents leveraging the Python SDK.
- **CLI Users:** Software engineers seeking a Claude Code-like terminal assistant.
- **Enterprise:** Organizations needing an enterprise-ready, locally configurable agent runner.

## Key Capabilities
- **Built-in Tools:** Out-of-the-box filesystem access (`read_file`, `write_file`, `grep`), shell execution (with sandboxing), and task planning (`write_todos`).
- **Sub-agents:** Delegation to specialized sub-agents with isolated context windows to handle complex tasks iteratively.
- **MCP Support:** Native support for Model Context Protocol (MCP) clients (`langchain-mcp-adapters`) to integrate external tools.

## Design Tenets
- **Trust the LLM:** The agent can do anything its tools allow; boundaries are enforced at the sandbox/tool level.
- **LangGraph Native:** Every agent is a compiled graph, fully compatible with LangSmith tracing and LangGraph Studio.
- **Provider Agnostic:** Works with any LLM provider that supports tool calling (e.g., Anthropic, OpenAI, Google Gemini).

## Extensibility Mechanisms
Users can customize and extend the framework's capabilities via:
- **Python Tools:** Injecting custom Python functions as tools via the SDK.
- **Markdown Skills:** Adding domain-specific knowledge and workflows via markdown SKILL files.
- **Custom Models:** Swapping in different LLM providers or models natively using `init_chat_model`.