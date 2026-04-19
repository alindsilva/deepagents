# Implementation Plan: Build lightweight mapping layer from docker-agent YAML to deepagents

## Phase 1: Project Setup and YAML Parsing
- [ ] Task: Write Tests for YAML parser
- [ ] Task: Implement basic YAML parser module
- [ ] Task: Conductor - User Manual Verification 'Phase 1: Project Setup and YAML Parsing' (Protocol in workflow.md)

## Phase 2: Tool and MCP Mapping
- [ ] Task: Write Tests for toolset resolution
- [ ] Task: Implement `resolve_tools` mapping standard toolsets to deepagents tools
- [ ] Task: Write Tests for MCP `docker:` ref parsing and StdioConnection creation
- [ ] Task: Implement custom MCP loader for docker-agent streamable/stdio transports
- [ ] Task: Conductor - User Manual Verification 'Phase 2: Tool and MCP Mapping' (Protocol in workflow.md)

## Phase 3: Agent Orchestration
- [ ] Task: Write Tests for sub-agent generation
- [ ] Task: Implement logic to dynamically build LangGraph sub-agents from YAML sub_agents dict
- [ ] Task: Write Tests for root agent construction
- [ ] Task: Implement root agent compilation and tool binding
- [ ] Task: Conductor - User Manual Verification 'Phase 3: Agent Orchestration' (Protocol in workflow.md)

## Phase 4: CLI Entry Point and Example
- [ ] Task: Write Tests for CLI entry point
- [ ] Task: Implement `main.py` entry point to execute the loaded agent graph
- [ ] Task: Create sample `team.yaml` for demonstration
- [ ] Task: Conductor - User Manual Verification 'Phase 4: CLI Entry Point and Example' (Protocol in workflow.md)