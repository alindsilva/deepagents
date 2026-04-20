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
            import uuid
            import os

            app = DeepAgentsApp(
                agent=graph,
                assistant_id=f"bridge-{uuid.uuid4().hex[:8]}",
                thread_id=str(uuid.uuid4()),
                backend=FilesystemBackend(root_dir=os.getcwd()),
                initial_prompt=args.query
            )
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
