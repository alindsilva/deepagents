import yaml
from typing import Any

def parse_yaml_config(yaml_string: str) -> dict[str, Any]:
    """Parse a docker-agent YAML configuration string into a dictionary.

    Args:
        yaml_string: The raw YAML string to parse.

    Returns:
        A dictionary containing the parsed configuration.

    Raises:
        ValueError: If the YAML string is empty or invalid.
    """
    if not yaml_string.strip():
        raise ValueError("Configuration is empty or invalid")

    try:
        config = yaml.safe_load(yaml_string)
    except yaml.YAMLError as exc:
        raise ValueError(f"Configuration is empty or invalid: {exc}") from exc

    if not isinstance(config, dict):
        raise ValueError("Configuration is empty or invalid")

    return config