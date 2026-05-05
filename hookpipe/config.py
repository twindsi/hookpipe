"""Configuration loader for hookpipe.

Loads route definitions from a YAML config file. Each route specifies
an incoming path, a target URL, optional filter rules, and optional
transformation rules.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml


DEFAULT_CONFIG_PATH = os.environ.get("HOOKPIPE_CONFIG", "hookpipe.yml")


class ConfigError(Exception):
    """Raised for invalid or missing configuration."""


def load_config(path: str | Path = DEFAULT_CONFIG_PATH) -> dict[str, Any]:
    """Load and validate the hookpipe YAML configuration.

    Expected top-level structure::

        routes:
          - path: /github
            target: https://example.com/hook
            filters:
              - field: action
                op: eq
                value: opened
            transforms:
              - set:
                  source: "hookpipe"

    Returns the parsed config dict.
    """
    config_path = Path(path)
    if not config_path.exists():
        raise ConfigError(f"Config file not found: {config_path}")

    with config_path.open("r") as fh:
        try:
            data = yaml.safe_load(fh)
        except yaml.YAMLError as exc:
            raise ConfigError(f"Failed to parse YAML config: {exc}") from exc

    if not isinstance(data, dict):
        raise ConfigError("Config must be a YAML mapping at the top level.")

    routes = data.get("routes")
    if not isinstance(routes, list) or len(routes) == 0:
        raise ConfigError("Config must contain a non-empty 'routes' list.")

    for i, route in enumerate(routes):
        if "path" not in route:
            raise ConfigError(f"Route #{i} is missing required field 'path'.")
        if "target" not in route:
            raise ConfigError(f"Route #{i} is missing required field 'target'.")

    return data
