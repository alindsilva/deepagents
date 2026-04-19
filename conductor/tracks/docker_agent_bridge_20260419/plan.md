# Implementation Plan: Build lightweight mapping layer from docker-agent YAML to deepagents

## Phase 1: Requirements Engineering
- [x] Task: Reverse engineer docker-agent YAML parser rules into a requirements document
- [ ] Task: Conductor - User Manual Verification 'Phase 1: Requirements Engineering' (Protocol in workflow.md)

## Phase 2: Project Setup & Scaffolding
- [ ] Task: Create `pyproject.toml` and directory structure
- [ ] Task: Write tests for YAML parser
- [ ] Task: Implement basic YAML parser module
- [ ] Task: Conductor - User Manual Verification 'Phase 2: Project Setup & Scaffolding' (Protocol in workflow.md)

## Phase 3: Model & Provider Initialization
- [ ] Task: Write tests for model resolution
- [ ] Task: Implement parser for `providers` and `models` YAML blocks
- [ ] Task: Conductor - User Manual Verification 'Phase 3: Model & Provider Initialization' (Protocol in workflow.md)

## Phase 4: Tool and MCP Mapping
- [ ] Task: Write tests for toolset resolution
- [ ] Task: Implement `resolve_tools` for standard deepagents tools
- [ ] Task: Write tests for MCP ref parsing (stdio/docker and streamable/remote)
- [ ] Task: Implement custom MCP loader for `docker-agent` formats
- [ ] Task: Conductor - User Manual Verification 'Phase 4: Tool and MCP Mapping' (Protocol in workflow.md)

## Phase 5: Agent Orchestration
- [ ] Task: Write tests for sub-agent and root agent generation
- [ ] Task: Implement logic to dynamically build LangGraph agents
- [ ] Task: Conductor - User Manual Verification 'Phase 5: Agent Orchestration' (Protocol in workflow.md)

## Phase 6: CLI Entry Point and Documentation
- [ ] Task: Implement `main.py` execution entry point
- [ ] Task: Create sample `team.yaml`
- [ ] Task: Write `README.md` documentation
- [ ] Task: Conductor - User Manual Verification 'Phase 6: CLI Entry Point and Documentation' (Protocol in workflow.md)