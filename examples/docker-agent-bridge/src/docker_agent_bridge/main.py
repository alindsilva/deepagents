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
    args = parser.parse_args()

    try:
        with open(args.config, "r") as f:
            yaml_content = f.read()

        config = parse_yaml_config(yaml_content)
        graph = await build_agent_graph(config)

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

        if not query or query.lower() in ["exit", "quit"]:
            return

        print(f"\n[Invoking Root Agent with query: {query}]")
        # Run the agent
        initial_state = {"messages": [{"role": "user", "content": query}]}
        result = await graph.ainvoke(initial_state)

        # Print final message content
        if "messages" in result and result["messages"]:
            last_message = result["messages"][-1]
            
            # Extract content string
            # Content can be a string or a list of dicts (for Gemini/Anthropic)
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
