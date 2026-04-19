# Product Guidelines: Deep Agents

## Voice and Tone
- **Direct & Professional:** Use a concise, professional tone suitable for software engineers and CLI environments. Avoid conversational filler or overly colloquial language.
- **High-Signal:** Focus exclusively on intent and technical rationale. Explain the "why" clearly and limit prose.
- **Developer-Centric:** Assume technical competence. Use standard industry terminology without over-explaining basic concepts.

## Design and UX Principles
- **Terminal-First (CLI):** The `deepagents-cli` should be responsive and visually appealing using the Textual framework. Prioritize fast startup, minimal dependencies on the hot path, and clear visual hierarchies.
- **Progressive Disclosure:** Expose advanced features (like custom tools, sub-agents, and complex LangGraph capabilities) only when needed, while keeping the "getting started" path simple.
- **Feedback & Transparency:** Agents must provide clear, actionable feedback to the user, especially when executing shell commands or making file system changes.

## Documentation
- **Google-Style Docstrings:** Use Google-style docstrings with comprehensive `Args`, `Returns`, and `Raises` sections for all public functions.
- **Explicit Types:** All Python code must include type hints. Avoid `Any`.
- **Actionable Examples:** Prefer short, working code examples in documentation to demonstrate usage patterns.

## Security & Privacy
- **Sandbox By Default:** Encourage the use of sandboxed environments (e.g., E2B, Daytona, Runloop) for code execution.
- **No Secret Logging:** Never log, print, or commit API keys, secrets, or sensitive configuration data.