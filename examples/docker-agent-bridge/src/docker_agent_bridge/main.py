import argparse
import sys
from docker_agent_bridge.parser import parse_yaml_config
from docker_agent_bridge.orchestration import build_agent_graph

def run_bridge():
    """CLI entry point for the docker-agent-bridge."""
    parser = argparse.ArgumentParser(description="Docker Agent to Deep Agents Bridge")
    parser.add_argument("config", help="Path to the docker-agent YAML config file")
    parser.add_argument("--query", help="Initial query for the agent", default=None)
    args = parser.parse_args()

    try:
        with open(args.config, "r") as f:
            yaml_content = f.read()

        config = parse_yaml_config(yaml_content)
        graph = build_agent_graph(config)

        query = args.query
        if not query:
            if not sys.stdin.isatty():
                print("Error: No query provided and stdin is not a TTY", file=sys.stderr)
                sys.exit(1)
            print("\nBridge ready. Type your query (or 'exit' to quit):")
            try:
                query = input("> ")
            except EOFError:
                return

        if query.lower() in ["exit", "quit"]:
            return

        print(f"\n[Invoking Root Agent with query: {query}]")
        # Run the agent
        # Note: LangGraph invoke returns the final state
        result = graph.invoke({"messages": [{"role": "user", "content": query}]})

        # Print final message content
        if "messages" in result and result["messages"]:
            last_message = result["messages"][-1]
            # Handle both BaseMessage objects and dicts if necessary
            content = getattr(last_message, "content", str(last_message))
            print(f"\nAgent Response:\n{content}")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    run_bridge()
