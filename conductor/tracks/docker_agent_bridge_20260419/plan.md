# Implementation Plan: Build lightweight mapping layer from docker-agent YAML to deepagents

> **CRITICAL INSTRUCTION FOR CONDUCTOR:**
> A corresponding `beads` (bd) issue hierarchy has already been created for this plan.
> Do NOT use markdown TODOs or generic task management tools.
> You MUST use the `bd ready`, `bd show <id>`, `bd update <id> --claim`, and `bd close <id>` commands to guide implementation and track progress according to the `bd prime` workflow.
> Ensure that all work is pushed to the remote (`bd dolt push` and `git push`) at the end of the session.

## Phase 1: Requirements Engineering
- [x] Task: Reverse engineer docker-agent YAML parser rules into a requirements document
- [ ] Task: Conductor - User Manual Verification 'Phase 1: Requirements Engineering' (Protocol in workflow.md)

## Phase 2: Project Setup & Scaffolding [checkpoint: e36c997f]
- [x] Task: Create `pyproject.toml` and directory structure bf4faf82
- [x] Task: Write tests for YAML parser ace13e7a
- [x] Task: Implement basic YAML parser module dbce8482
- [x] Task: Conductor - User Manual Verification 'Phase 2: Project Setup & Scaffolding' (Protocol in workflow.md) e36c997f

## Phase 3: Model & Provider Initialization [checkpoint: 943ae37c]
- [x] Task: Write tests for model resolution 794a366e
- [x] Task: Implement parser for `providers` and `models` YAML blocks 02801673
- [x] Task: Conductor - User Manual Verification 'Phase 3: Model & Provider Initialization' (Protocol in workflow.md) 943ae37c

## Phase 4: Tool and MCP Mapping [checkpoint: 29e3748a]
- [x] Task: Write tests for toolset resolution 18f5b042
- [x] Task: Implement resolve_tools for standard deepagents tools c5f83c8b
- [x] Task: Write tests for MCP ref parsing (stdio/docker and streamable/remote) 9a00ae51
- [x] Task: Implement custom MCP loader for docker-agent formats 05623756
- [x] Task: Conductor - User Manual Verification 'Phase 4: Tool and MCP Mapping' (Protocol in workflow.md) 29e3748a

## Phase 5: Agent Orchestration [checkpoint: 19751a6f]
- [x] Task: Write tests for sub-agent and root agent generation 2b1c16fd
- [x] Task: Implement logic to dynamically build LangGraph agents a61dfd0e
- [x] Task: Conductor - User Manual Verification 'Phase 5: Agent Orchestration' (Protocol in workflow.md) 19751a6f

## Phase 6: CLI Entry Point and Documentation
- [ ] Task: Implement `main.py` execution entry point
- [ ] Task: Create sample `team.yaml`
- [ ] Task: Write `README.md` documentation
- [ ] Task: Conductor - User Manual Verification 'Phase 6: CLI Entry Point and Documentation' (Protocol in workflow.md)

## Phase 7: Example Parity and Validation
- [ ] Task: Bootstrap a simple YAML file from `docker-agent` examples and verify execution
- [ ] Task: Translate an existing `deepagents` example into YAML and verify execution parity
- [ ] Task: Conductor - User Manual Verification 'Phase 7: Example Parity and Validation' (Protocol in workflow.md)