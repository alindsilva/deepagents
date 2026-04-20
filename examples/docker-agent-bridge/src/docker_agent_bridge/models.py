import os
from dataclasses import dataclass
from typing import Any, Optional
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
    """Register dynamic profiles for custom providers like Cloudflare."""
    _register_harness_profile(
        "cloudflare",
        _HarnessProfile(init_kwargs={"use_responses_api": False, "store": False})
    )

# Initialize custom profiles on module load
register_custom_profiles()

@dataclass
class GatewayConfig:
    """Standardized gateway configuration resolved from YAML."""
    effective_provider: str
    model_name: str
    base_url: Optional[str]
    is_gateway: bool

class GatewayResolver:
    """Helper that formalizes Cloudflare and other gateway resolution patterns."""
    
    @staticmethod
    def resolve(base_url: Optional[str], model_name: str, provider_name: str) -> GatewayConfig:
        is_gateway = base_url and any(x in base_url for x in ["gateway", "cloudflare", "openclaw"])
        
        if not is_gateway:
            # Not a gateway, use standard detection (handled in resolve_models)
            return GatewayConfig(effective_provider="", model_name=model_name, base_url=base_url, is_gateway=False)

        # Standardize Cloudflare endpoints
        if "gateway.ai.cloudflare.com" in base_url:
            parts = base_url.split("/")
            if len(parts) >= 6 and not ("/compat" in base_url or "/openai" in base_url or "/anthropic" in base_url or "/google" in base_url):
                 # Default to /compat for unspecialized cloudflare URLs
                 base_url = "/".join(parts[:6]) + "/compat"

        # 1. OpenAI Compatibility (/compat)
        if base_url.endswith("/compat") or base_url.endswith("/compat/"):
            prefix = "openai"
            if any(x in base_url or x in provider_name for x in ["google", "gemini"]):
                prefix = "google-ai-studio"
            elif any(x in base_url or x in provider_name for x in ["anthropic"]):
                prefix = "anthropic"
            elif any(x in base_url or x in provider_name for x in ["mistral"]):
                prefix = "mistral"
            
            standardized_model = f"{prefix}/{model_name}" if "/" not in model_name else model_name
            return GatewayConfig(effective_provider="openai", model_name=standardized_model, base_url=base_url, is_gateway=True)

        # 2. Native Gateway Endpoints
        if "anthropic" in base_url:
            return GatewayConfig(effective_provider="anthropic", model_name=model_name, base_url=base_url, is_gateway=True)
        if "google" in base_url or "gemini" in base_url:
            return GatewayConfig(effective_provider="google_genai", model_name=model_name, base_url=base_url, is_gateway=True)

        # Fallback to OpenAI for unknown gateways
        return GatewayConfig(effective_provider="openai", model_name=model_name, base_url=base_url, is_gateway=True)

def resolve_models(config: dict[str, Any]) -> dict[str, Any]:
    """Parse providers and models blocks into LangChain chat models."""
    providers = config.get("providers", {})
    models_config = config.get("models", {})
    resolved_models = {}

    for name, model_data in models_config.items():
        provider_name = model_data.get("provider")
        model_name = model_data.get("model")
        resolved_config = model_data.copy()
        
        # Merge Provider Defaults
        if provider_name in providers:
            p_cfg = providers[provider_name]
            resolved_config.setdefault("base_url", p_cfg.get("base_url"))
            resolved_config.setdefault("api_type", p_cfg.get("api_type"))
            headers = p_cfg.get("headers", {}).copy()
            headers.update(resolved_config.get("headers", {}))
            resolved_config["headers"] = headers
        elif provider_name in ALIASES:
            alias = ALIASES[provider_name]
            resolved_config.setdefault("base_url", alias["base_url"])
            resolved_config.setdefault("api_type", alias["api_type"])

        # Determine Effective Provider and Gateway Logic
        base_url = interpolate_env_vars(resolved_config.get("base_url")) if resolved_config.get("base_url") else None
        gw = GatewayResolver.resolve(base_url, model_name, provider_name)
        
        effective_provider = gw.effective_provider or resolved_config.get("api_type") or provider_name
        model_name = gw.model_name
        base_url = gw.base_url

        # Normalize Provider Names
        provider_map = {"openai_chatcompletions": "openai", "openai_responses": "openai", "google": "google_genai", "dmr": "openai"}
        effective_provider = provider_map.get(effective_provider, effective_provider)

        # Interpolate and Extract Headers/Auth
        headers = {k: interpolate_env_vars(v) for k, v in resolved_config.get("headers", {}).items()}
        api_key = None
        
        if gw.is_gateway and effective_provider == "openai" and "cf-aig-authorization" in headers:
            api_key = headers["cf-aig-authorization"].removeprefix("Bearer ")
        
        if not api_key:
            api_key = headers.get("x-goog-api-key") or headers.get("Authorization", "").removeprefix("Bearer ") or None
            
        if not api_key:
            env_map = {"openai": ["OPENAI_API_KEY", "CF_AIG_TOKEN"], "anthropic": ["ANTHROPIC_API_KEY"], "google_genai": ["GOOGLE_API_KEY"]}
            for env_var in env_map.get(effective_provider, []):
                if val := os.environ.get(env_var):
                    api_key = val
                    break

        try:
            model_args = {
                "model": model_name,
                "model_provider": effective_provider,
                "temperature": resolved_config.get("temperature"),
                "max_tokens": resolved_config.get("max_tokens"),
                "base_url": base_url.rstrip("/") if base_url else None
            }

            if api_key:
                key_field = "google_api_key" if effective_provider == "google_genai" else "api_key"
                model_args[key_field] = api_key

            if effective_provider == "google_genai":
                filtered_headers = {k: v for k, v in headers.items() if k.lower() not in ["x-goog-api-key", "authorization"]}
                if filtered_headers:
                    model_args["additional_headers"] = filtered_headers
            elif headers:
                model_args["default_headers"] = headers

            from deepagents.profiles import _get_harness_profile
            profile = _get_harness_profile("cloudflare" if gw.is_gateway else effective_provider)
            init_kwargs = {**profile.init_kwargs}
            if profile.init_kwargs_factory:
                init_kwargs.update(profile.init_kwargs_factory())
            if gw.is_gateway:
                init_kwargs = {k: v for k, v in init_kwargs.items() if v is not False}

            provider_opts = resolved_config.get("provider_opts", {}).copy()
            if effective_provider != "anthropic":
                provider_opts.pop("service_tier", None)

            resolved_models[name] = init_chat_model(**model_args, **init_kwargs, **provider_opts)
        except Exception as e:
            print(f"Warning: Failed to initialize '{name}': {e}")
            resolved_models[name] = e

    return resolved_models
