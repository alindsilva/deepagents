import os
import re

def interpolate_env_vars(text: str) -> str:
    """Replace ${VAR_NAME} placeholders with environment variables."""
    def replace_match(match):
        var_name = match.group(1)
        value = os.environ.get(var_name)
        if value is None:
            raise ValueError(f"Environment variable {var_name} not found")
        return value

    return re.sub(r"\$\{([^}]+)\}", replace_match, text)
