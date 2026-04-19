import os
import re
from typing import Any
from langchain.chat_models import init_chat_model

def interpolate_env_vars(text: str) -> str:
    """Replace ${VAR_NAME} placeholders with environment variables."""
    def replace_match(match):
        var_name = match.group(1)
        value = os.environ.get(var_name)
        if value is None:
            raise ValueError(f"Environment variable {var_name} not found")
        return value

    return re.sub(r"\$\{([^}]+)\}", replace_match, text)

def resolve_models(config: dict[str, Any]) -> dict[str, Any]:
    """Parse providers and models blocks into LangChain chat models.

    Args:
        config: The parsed YAML configuration.

    Returns:
        A mapping of model names to instantiated LangChain chat models.
    """
    providers = config.get("providers", {})
    models_config = config.get("models", {})
    resolved_models = {}

    for name, model_data in models_config.items():
        provider_ref = model_data.get("provider")
        model_name = model_data.get("model")
        
        # Start with model-level config
        resolved_config = model_data.copy()
        
        # Merge with provider defaults if it's a reference to the providers block
        if provider_ref in providers:
            provider_data = providers[provider_ref]
            for key in ["base_url", "headers", "api_type"]:
                if key in provider_data and key not in model_data:
                    resolved_config[key] = provider_data[key]
            
            # Use the provider's inferred api type / actual provider if needed
            # For simplicity in this bridge, we'll assume the provider_ref is the provider name
            # unless it's a key in the providers block.
            # In the schema, providers define reusable defaults.
            # If provider_ref is "cloudflare" (a key in providers), the actual model provider
            # is usually embedded in the base_url or specified elsewhere.
            # LangChain's init_chat_model needs the actual provider (openai, anthropic, etc.)
            
            # Heuristic: if base_url contains 'anthropic', 'openai', 'google', use that.
            # This is a bit manual, but maps to common custom gateway patterns.
        
        # Interpolate environment variables in base_url and headers
        if "base_url" in resolved_config:
            resolved_config["base_url"] = interpolate_env_vars(resolved_config["base_url"])
            
        if "headers" in resolved_config:
            new_headers = {}
            for k, v in resolved_config["headers"].items():
                new_headers[k] = interpolate_env_vars(v)
            resolved_config["headers"] = new_headers

        # Instantiate LangChain Chat Model
        # We'll use init_chat_model which handles provider detection and mapping
        
        # Extraction logic for provider name if it was a reference
        # Standard docker-agent: "provider" is the name of the LLM provider (openai, anthropic)
        # OR a key in the "providers" map.
        actual_provider = provider_ref
        if provider_ref in providers:
            # If it's a custom provider, we need to know what it is (e.g., openai compatible)
            # Default to openai for gateways unless otherwise specified
            actual_provider = "openai"
            if "anthropic" in resolved_config.get("base_url", ""):
                actual_provider = "anthropic"

        model = init_chat_model(
            model=model_name,
            model_provider=actual_provider,
            temperature=resolved_config.get("temperature"),
            max_tokens=resolved_config.get("max_tokens"),
            base_url=resolved_config.get("base_url"),
            default_headers=resolved_config.get("headers"),
            **resolved_config.get("provider_opts", {})
        )
        
        resolved_models[name] = model

    return resolved_models
