"""Load and validate hookpipe configuration."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class ConfigError(Exception):
    """Raised when configuration is invalid."""


def _validate_target(target: Any, index: int) -> None:
    if not isinstance(target, dict):
        raise ConfigError(f"targets[{index}] must be a dict")
    if "url" not in target:
        raise ConfigError(f"targets[{index}] missing required field 'url'")
    if not isinstance(target["url"], str) or not target["url"].startswith("http"):
        raise ConfigError(f"targets[{index}]['url'] must be an HTTP/HTTPS URL")


def _validate_route(route: Any, index: int) -> None:
    if not isinstance(route, dict):
        raise ConfigError(f"routes[{index}] must be a dict")
    if "targets" not in route:
        raise ConfigError(f"routes[{index}] missing required field 'targets'")
    if not isinstance(route["targets"], list):
        raise ConfigError(f"routes[{index}]['targets'] must be a list")
    for t_idx, target in enumerate(route["targets"]):
        _validate_target(target, t_idx)
    filters = route.get("filters", [])
    if not isinstance(filters, list):
        raise ConfigError(f"routes[{index}]['filters'] must be a list")


def _validate_config(config: Any) -> None:
    if not isinstance(config, dict):
        raise ConfigError("config must be a JSON object")
    if "routes" not in config:
        raise ConfigError("config missing required field 'routes'")
    if not isinstance(config["routes"], list):
        raise ConfigError("'routes' must be a list")
    for idx, route in enumerate(config["routes"]):
        _validate_route(route, idx)


def load_config(path: str | Path) -> dict[str, Any]:
    """Load and validate a JSON config file.

    Args:
        path: Path to the JSON configuration file.

    Returns:
        Validated configuration dict.

    Raises:
        ConfigError: If the file cannot be read, parsed, or is structurally
                     invalid.
    """
    try:
        raw = Path(path).read_text(encoding="utf-8")
    except OSError as exc:
        raise ConfigError(f"Cannot read config file: {exc}") from exc

    try:
        config = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ConfigError(f"Config is not valid JSON: {exc}") from exc

    _validate_config(config)
    return config
