import argparse
import sys
import asyncio
from docker_agent_bridge.parser import parse_yaml_config
from docker_agent_bridge.orchestration import build_agent_graph
from docker_agent_bridge.models import resolve_models

async def _run_bridge():
    """CLI entry point for the docker-agent-bridge."""
    import warnings
    # Suppress noisy LangChain warnings about provider-specific parameters
    warnings.filterwarnings("ignore", message=".*service_tier.*", category=UserWarning)
    
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
            from docker_agent_bridge.adapter import run_bridge_tui
            resolved_models = resolve_models(config)
            await run_bridge_tui(graph, resolved_models, initial_prompt=args.query)
            return

        # Maintain session state for basic CLI loop
        state = {"messages": []}
        initial_query = args.query
        
        print("\nBridge ready. Type your query (or 'exit' to quit):")

        while True:
            if initial_query:
                query = initial_query
                initial_query = None 
            else:
                try:
                    query = input("\n> ")
                except EOFError:
                    break

            if not query or query.lower() in ["exit", "quit"]:
                break

            print(f"\n[Invoking Root Agent...]")
            state["messages"].append({"role": "user", "content": query})
            state = await graph.ainvoke(state)

            if "messages" in state and state["messages"]:
                last_message = state["messages"][-1]
                raw_content = getattr(last_message, "content", "")
                
                if isinstance(raw_content, list):
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
