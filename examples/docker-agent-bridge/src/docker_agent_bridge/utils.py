import os
import re

def interpolate_env_vars(text: str) -> str:
    """Replace ${VAR_NAME} or ${env.VAR_NAME} placeholders with environment variables."""
    def replace_match(match):
        var_name = match.group(1)
        # Strip 'env.' prefix if present
        lookup_name = var_name[4:] if var_name.startswith("env.") else var_name
        value = os.environ.get(lookup_name)
        if value is None:
            raise ValueError(f"Environment variable {lookup_name} not found")
        return value

    return re.sub(r"\$\{([^}]+)\}", replace_match, text)
