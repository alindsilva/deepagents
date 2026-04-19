import os
from typing import Any
from langchain.chat_models import init_chat_model
from docker_agent_bridge.utils import interpolate_env_vars
from deepagents.profiles._harness_profiles import _HarnessProfile, _register_harness_profile

# Provider Aliases from docker-agent
ALIASES = {
    "requesty": {"api_type": "openai", "base_url": "https://router.requesty.ai/v1", "token_env": "REQUESTY_API_KEY"},
    "xai": {"api_type": "openai", "base_url": "https://api.x.ai/v1", "token_env": "XAI_API_KEY"},
    "nebius": {"api_type": "openai", "base_url": "https://api.studio.nebius.com/v1", "token_env": "NEBIUS_API_KEY"},
    "mistral": {"api_type": "openai", "base_url": "https://api.mistral.ai/v1", "token_env": "MISTRAL_API_KEY"},
    "ollama": {"api_type": "openai", "base_url": "http://localhost:11434/v1", "token_env": None},
    "minimax": {"api_type": "openai", "base_url": "https://api.minimax.io/v1", "token_env": "MINIMAX_API_KEY"},
}

def register_custom_profiles():
    """Register dynamic profiles for custom providers like Cloudflare.
    
    This ensures that deepagents middleware and initialization logic doesn't
    inject provider-specific parameters (like OpenAI's Responses API) that
    custom gateways don't support.
    """
    # Cloudflare Gateway Profile
    _register_harness_profile(
        "cloudflare",
        _HarnessProfile(
            init_kwargs={
                "use_responses_api": False,
                "store": False,
            }
        )
    )

# Initialize custom profiles on module load
register_custom_profiles()

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
        provider_name = model_data.get("provider")
        model_name = model_data.get("model")
        
        # 1. Start with base config
        resolved_config = model_data.copy()
        
        # 2. Apply Custom Provider Defaults
        if provider_name in providers:
            p_config = providers[provider_name]
            if not resolved_config.get("base_url") and p_config.get("base_url"):
                resolved_config["base_url"] = p_config["base_url"]
            
            merged_headers = p_config.get("headers", {}).copy()
            merged_headers.update(resolved_config.get("headers", {}))
            resolved_config["headers"] = merged_headers
            
            if "api_type" not in resolved_config and p_config.get("api_type"):
                resolved_config["api_type"] = p_config["api_type"]
        
        # 3. Apply Built-in Alias Defaults
        elif provider_name in ALIASES:
            alias = ALIASES[provider_name]
            if not resolved_config.get("base_url"):
                resolved_config["base_url"] = alias["base_url"]
            if "api_type" not in resolved_config:
                resolved_config["api_type"] = alias["api_type"]

        # 4. Resolve Effective Provider / API Type
        api_type = resolved_config.get("api_type")
        effective_provider = api_type if api_type else provider_name
        
        if effective_provider in ["openai_chatcompletions", "openai_responses"]:
            effective_provider = "openai"
        elif effective_provider == "google":
            effective_provider = "google_genai"
        elif effective_provider == "dmr":
            effective_provider = "openai"
        
        # 5. Interpolation
        base_url = resolved_config.get("base_url")
        if base_url:
            base_url = interpolate_env_vars(base_url)
        
        headers = resolved_config.get("headers", {})
        interpolated_headers = {}
        for k, v in headers.items():
            interpolated_headers[k] = interpolate_env_vars(v)

        # 6. Gateway Logic Override
        is_gateway = base_url and ("gateway" in base_url or "cloudflare" in base_url or "openclaw" in base_url)
        
        if is_gateway:
            # Check if this is a native Anthropic gateway endpoint
            if "anthropic" in base_url and not ("/compat" in base_url or "/openai" in base_url):
                effective_provider = "anthropic"
            else:
                effective_provider = "openai"
                
                if "gateway.ai.cloudflare.com" in base_url:
                    parts = base_url.split("/")
                    if len(parts) >= 6:
                        base_url = "/".join(parts[:6]) + "/compat"
                
                if "/compat" in base_url:
                    prefix = "openai"
                    if "google" in base_url or "gemini" in base_url or "google" in provider_name:
                        prefix = "google-ai-studio"
                    elif "anthropic" in base_url or "anthropic" in provider_name:
                        prefix = "anthropic"
                    elif "mistral" in base_url or "mistral" in provider_name:
                        prefix = "mistral"
                    
                    if "/" not in model_name:
                        model_name = f"{prefix}/{model_name}"

            if base_url:
                base_url = base_url.replace("/chat/completions", "").rstrip("/")

        # 7. Authentication Extraction
        api_key = None
        # Try to find a provider API key explicitly passed in headers
        if "x-goog-api-key" in interpolated_headers:
            api_key = interpolated_headers.pop("x-goog-api-key")
        elif "Authorization" in interpolated_headers:
            auth = interpolated_headers.pop("Authorization")
            if auth.startswith("Bearer "):
                api_key = auth[7:]
            else:
                api_key = auth
        
        # If no key found in headers, fallback to environment
        if not api_key:
            if effective_provider == "openai":
                api_key = os.environ.get("OPENAI_API_KEY")
            elif effective_provider == "anthropic":
                api_key = os.environ.get("ANTHROPIC_API_KEY")
            elif effective_provider == "google_genai":
                api_key = os.environ.get("GOOGLE_API_KEY")
        
        # SPECIAL CASE: For gateways using OpenAI provider, the API key might need
        # to be the gateway token itself if the backend auth is handled by Cloudflare.
        # But for /compat endpoint, we usually pass the actual backend key.
        # We'll stick to the actual backend keys for now as sourced from .env.

        try:
            masked_key = f"{api_key[:6]}...{api_key[-4:]}" if api_key and len(api_key) > 10 else "NONE"
            print(f"[Bridge] Initializing model '{name}': provider={effective_provider}, model={model_name}, api_key={masked_key}, base_url={base_url}")
            
            pass_headers = interpolated_headers if effective_provider not in ["google_genai"] else None

            from deepagents.profiles import _get_harness_profile
            profile_key = "cloudflare" if is_gateway else effective_provider
            profile = _get_harness_profile(profile_key)
            
            init_kwargs = {**profile.init_kwargs}
            if profile.init_kwargs_factory:
                init_kwargs.update(profile.init_kwargs_factory())
            
            if is_gateway:
                init_kwargs = {k: v for k, v in init_kwargs.items() if v is not False}

            model = init_chat_model(
                model=model_name,
                model_provider=effective_provider,
                api_key=api_key,
                temperature=resolved_config.get("temperature"),
                max_tokens=resolved_config.get("max_tokens"),
                base_url=base_url,
                default_headers=pass_headers,
                **init_kwargs,
                **resolved_config.get("provider_opts", {})
            )
            resolved_models[name] = model
        except Exception as e:
            print(f"Warning: Failed to initialize '{name}': {e}")
            resolved_models[name] = e

    return resolved_models
