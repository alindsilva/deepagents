import subprocess
import asyncio
from typing import Any
from langchain_core.tools import BaseTool, StructuredTool
from pydantic import create_model

def create_shell_script_tool(name: str, config: dict[str, Any]) -> BaseTool:
    """Create a StructuredTool that executes a shell command."""
    cmd_template = config.get("cmd", "")
    description = config.get("description", "")
    args_config = config.get("args", {})

    # Dynamically create a Pydantic model for the tool's arguments
    fields = {}
    for arg_name, arg_info in args_config.items():
        arg_type = str
        if isinstance(arg_info, dict) and arg_info.get("type") == "integer":
            arg_type = int
        
        fields[arg_name] = (arg_type, ...)

    ArgsModel = create_model(f"{name}Args", **fields)

    def run_cmd(**kwargs: Any) -> str:
        """Execute the shell command with provided arguments."""
        cmd = cmd_template
        for k, v in kwargs.items():
            if v is not None:
                cmd = cmd.replace(f"${k}", str(v))

        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout
        else:
            return f"Error: {result.stderr}"

    async def arun_cmd(**kwargs: Any) -> str:
        """Execute the shell command asynchronously."""
        cmd = cmd_template
        for k, v in kwargs.items():
            if v is not None:
                cmd = cmd.replace(f"${k}", str(v))

        process = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0:
            return stdout.decode()
        else:
            return f"Error: {stderr.decode()}"

    return StructuredTool.from_function(
        func=run_cmd,
        coroutine=arun_cmd,
        name=name,
        description=description,
        args_schema=ArgsModel
    )

async def resolve_tools(toolsets_config: list[dict[str, Any]]) -> list[BaseTool]:
    """Resolve local docker-agent toolsets (like script) into Deep Agents tools.

    Args:
        toolsets_config: The toolsets block from an agent configuration.

    Returns:
        A list of LangChain BaseTool instances.
    """
    tools = []
    
    for toolset in toolsets_config:
        t_type = toolset.get("type")

        if t_type == "script":
            shell_configs = toolset.get("shell", {})
            for name, config in shell_configs.items():
                tools.append(create_shell_script_tool(name, config))

    return tools
