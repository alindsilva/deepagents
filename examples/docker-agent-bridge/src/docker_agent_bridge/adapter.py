import uuid
import os
import contextlib
from typing import AsyncIterator, Any, Callable
from deepagents_cli.remote_client import RemoteAgent
from deepagents_cli.config import ModelResult
import deepagents_cli.config as cli_config

class BridgeRemoteAgent(RemoteAgent):
    """Proxy that allows a local graph to satisfy the TUI's RemoteAgent interface.
    
    This unlocks features like /model, /clear, and /threads in the professional TUI.
    """
    def __init__(self, graph: Any):
        # Initialize RemoteAgent with dummy data
        super().__init__(url="http://local-bridge")
        self._graph = graph

    async def astream(self, input: Any, stream_mode: list[str] | None = None, config: dict[str, Any] | None = None, context: Any | None = None, **kwargs: Any) -> AsyncIterator:
        # Normalize local graph (ns, mode, data) format for the TUI
        async for mode, data in self._graph.astream(
            input, 
            stream_mode=stream_mode or ["messages", "updates"],
            config=config,
            context=context
        ):
            yield ((), mode, data)

    async def aget_state(self, config: dict[str, Any]) -> Any:
        return await self._graph.aget_state(config)

    async def aupdate_state(self, config: dict[str, Any], values: dict[str, Any]) -> None:
        return await self._graph.aupdate_state(config, values)

    async def aensure_thread(self, config: dict[str, Any]) -> None:
        pass # Local graphs don't require explicit thread registration

    def with_config(self, config: dict[str, Any]) -> "BridgeRemoteAgent":
        return self

@contextlib.contextmanager
def patch_tui_model_resolution(resolved_models: dict[str, Any]):
    """Context manager that monkey-patches cli_config.create_model.
    
    This allows the TUI to resolve custom models defined in the bridge's YAML
    during runtime model switches (/model).
    """
    original_create_model = cli_config.create_model

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
    try:
        yield
    finally:
        cli_config.create_model = original_create_model

async def run_bridge_tui(graph: Any, resolved_models: dict[str, Any], initial_prompt: str | None = None):
    """Launch the Deep Agents TUI using the bridge adapter."""
    from deepagents_cli.app import DeepAgentsApp
    from deepagents.backends import FilesystemBackend
    
    app = DeepAgentsApp(
        agent=BridgeRemoteAgent(graph),
        assistant_id=f"bridge-{uuid.uuid4().hex[:8]}",
        thread_id=str(uuid.uuid4()),
        backend=FilesystemBackend(root_dir=os.getcwd(), virtual_mode=False),
        initial_prompt=initial_prompt
    )
    
    with patch_tui_model_resolution(resolved_models):
        await app.run_async()
