# Deep Agents: Monorepo Context & Guidelines

Deep Agents is an opinionated, ready-to-run agent harness built on [LangGraph](https://langchain-ai.github.io/langgraph/). It provides out-of-the-box planning, filesystem access, shell execution, and sub-agent delegation.

## Project Overview

- **Core SDK (`libs/deepagents`)**: The primary library for creating agents with `create_deep_agent`. It manages planning (`write_todos`), context windowing, and tool execution.
- **CLI Agent (`libs/cli`)**: A Textual-based interactive terminal UI (`deepagents-cli`) that provides a persistent coding assistant.
- **ACP Integration (`libs/acp`)**: Implements the [Agent Client Protocol](https://agentclientprotocol.com/), enabling Deep Agents to work as backends for editors like Zed.
- **Evals (`libs/evals`)**: An evaluation suite for measuring agent performance.

### Tech Stack
- **Language**: Python 3.11+
- **Orchestration**: LangChain & LangGraph
- **TUI Framework**: [Textual](https://textual.textualize.io/) (for the CLI)
- **Tooling**: `uv` (package manager), `ruff` (lint/format), `ty` (type checking), `make` (task runner).

## Building and Running

The project uses `uv` for dependency management and `make` for common tasks. Commands should generally be run from the relevant package directory in `libs/`.

- **Install Dependencies**: `uv sync` (run in the package directory).
- **Run Tests**: `make test` (unit tests, no network) or `make integration_test` (network allowed).
- **Lint & Type Check**: `make lint` (runs `ruff` and `ty`).
- **Format Code**: `make format`.
- **Run CLI**: `uv run deepagents` (inside `libs/cli`).

## Development Conventions

### 1. Code Standards & Typing
- **Strict Typing**: All functions MUST have type hints for arguments and return values. Avoid `Any`.
- **Docstrings**: Use **Google-style** docstrings. Document "why" rather than just "what".
- **Naming**: Use descriptive, self-explanatory names. Prefer single-word variable names where they are idiomatic.
- **Public APIs**: Maintain stable interfaces. Use keyword-only arguments for new parameters to avoid breaking changes.

### 2. Linting (Ruff)
- **Inline Suppression**: Use `# noqa: RULE` with a justifying comment for specific exceptions.
- **Categorical Policy**: Only use `per-file-ignores` in `pyproject.toml` for class-wide rules (e.g., ignoring docstring requirements in tests).

### 3. Testing
- **Structure**: Mirror the source code structure in `tests/`.
- **Unit vs. Integration**:
    - `tests/unit_tests/`: No network calls. Fast and deterministic.
    - `tests/integration_tests/`: Network calls allowed (e.g., to LLM providers).
- **Async**: `pytest-asyncio` is configured to "auto" mode; do not add `@pytest.mark.asyncio` manually.

### 4. CLI & TUI (Textual)
- **Startup Performance**: **CRITICAL**. Defer heavy imports (like `deepagents` or `langchain`) inside functions. Never import them at the module level in the startup path.
- **Textual Styles**: Prefer `textual.content.Content` over Rich `Text` for widgets.
- **Rich Markup**: Never use f-string interpolation in Rich markup (e.g., `f"[bold]{var}[/bold]"`). Use `Content.from_markup("[bold]$var[/bold]", var=value)` to ensure proper escaping of user-controlled content.

### 5. Commits & PRs
- **Conventional Commits**: Use `type(scope): message` format in lowercase (e.g., `feat(sdk): add...`).
- **Scopes**: PR titles must include a scope corresponding to the modified package (e.g., `sdk`, `cli`, `acp`, `evals`).

## Security
- **Trust the LLM**: Boundaries should be enforced at the tool/sandbox level, not by model instructions.
- **Secrets**: Never hardcode or log API keys. Use environment variables.
