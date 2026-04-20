import argparse
import sys
import asyncio
from docker_agent_bridge.parser import parse_yaml_config
from docker_agent_bridge.orchestration import build_agent_graph

async def _run_bridge():
    """CLI entry point for the docker-agent-bridge."""
    parser = argparse.ArgumentParser(description="Docker Agent to Deep Agents Bridge")
    parser.add_argument("config", help="Path to the docker-agent YAML config file")
    parser.add_argument("--query", help="Initial query for the agent", default=None)
    parser.add_argument("--tui", action="store_true", help="Launch the full terminal UI")
    args = parser.parse_args()

    try:
        with open(args.config, "r") as f:
            yaml_content = f.read()

        config = parse_yaml_config(yaml_content)
        graph = await build_agent_graph(config)

        # Handle TUI mode
        if args.tui:
            from deepagents_cli.app import DeepAgentsApp
            from deepagents.backends import FilesystemBackend
            from deepagents_cli.config import ModelResult
            import deepagents_cli.config as cli_config
            import uuid
            import os
            from typing import AsyncIterator

            # 1. Monkey-patch create_model to support bridge-resolved models
            original_create_model = cli_config.create_model
            resolved_models = resolve_models(config)

            def bridge_create_model(model_spec=None, **kwargs):
                if model_spec in resolved_models:
                    model = resolved_models[model_spec]
                    if not isinstance(model, Exception):
                        return ModelResult(
                            model=model,
                            model_name=model_spec,
                            provider="bridge",
                            context_limit=128000
                        )
                return original_create_model(model_spec, **kwargs)

            cli_config.create_model = bridge_create_model

            # 2. BridgeRemoteAgent to mimic a server-backed session
            class BridgeRemoteAgent:
                def __init__(self, graph):
                    self._graph = graph

                async def astream(self, input, stream_mode=None, config=None, context=None, **kwargs) -> AsyncIterator:
                    # RemoteAgent.astream yields (ns, mode, data)
                    # Local graph.astream yields (mode, data) OR messages depending on mode
                    # The TUI expects ns-tuple as first element
                    async for mode, data in self._graph.astream(
                        input, 
                        stream_mode=stream_mode or ["messages", "updates"],
                        config=config,
                        context=context
                    ):
                        yield ((), mode, data)

                async def aget_state(self, config):
                    return await self._graph.aget_state(config)

                async def aupdate_state(self, config, values):
                    return await self._graph.aupdate_state(config, values)

                async def aensure_thread(self, config):
                    pass # Not needed for local graph

                def with_config(self, config):
                    return self

            app = DeepAgentsApp(
                agent=BridgeRemoteAgent(graph),
                assistant_id=f"bridge-{uuid.uuid4().hex[:8]}",
                thread_id=str(uuid.uuid4()),
                backend=FilesystemBackend(root_dir=os.getcwd(), virtual_mode=False),
                initial_prompt=args.query
            )
            
            # 3. Hack: Force _remote_agent to return our proxy so /model works
            # DeepAgentsApp.action_switch_model checks isinstance(self._agent, RemoteAgent)
            # but we can't easily inherit because of heavy dependencies.
            # Instead, we just make our object look like it.
            from deepagents_cli.remote_client import RemoteAgent
            BridgeRemoteAgent.__bases__ = (RemoteAgent,)

            await app.run_async()
            return

        # Maintain session state for basic CLI loop
        state = {"messages": []}
        
        # Handle initial query if provided
        initial_query = args.query
        
        print("\nBridge ready. Type your query (or 'exit' to quit):")

        while True:
            if initial_query:
                query = initial_query
                initial_query = None # Clear after first turn
            else:
                try:
                    query = input("\n> ")
                except EOFError:
                    break

            if not query or query.lower() in ["exit", "quit"]:
                break

            print(f"\n[Invoking Root Agent...]")
            
            # Update state with new user message
            state["messages"].append({"role": "user", "content": query})
            
            # Run the agent (ainvoke returns final state)
            state = await graph.ainvoke(state)

            # Print final message content
            if "messages" in state and state["messages"]:
                last_message = state["messages"][-1]
                
                # Extract content string
                raw_content = getattr(last_message, "content", "")
                
                if isinstance(raw_content, list):
                    # Join all text blocks, ignoring metadata/signatures
                    content = "\n".join(
                        block["text"] for block in raw_content 
                        if isinstance(block, dict) and block.get("type") == "text"
                    )
                else:
                    content = str(raw_content)

                print(f"\nAgent Response:\n{content}")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

def run_bridge():
    asyncio.run(_run_bridge())

if __name__ == "__main__":
    run_bridge()
 as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

def run_bridge():
    asyncio.run(_run_bridge())

if __name__ == "__main__":
    run_bridge()
