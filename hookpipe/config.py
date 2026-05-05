"""Configuration loading and validation for hookpipe."""

import os
from typing import Any, Dict, List, Optional

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore


class ConfigError(Exception):
    """Raised when configuration is invalid or missing required fields."""


_REQUIRED_TARGET_KEYS = {"url"}
_VALID_METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE"}


def _validate_target(target: Dict[str, Any], index: int) -> None:
    missing = _REQUIRED_TARGET_KEYS - target.keys()
    if missing:
        raise ConfigError(f"Target[{index}] missing required keys: {missing}")
    method = target.get("method", "POST").upper()
    if method not in _VALID_METHODS:
        raise ConfigError(f"Target[{index}] unsupported method: {method!r}")


def _validate_config(config: Dict[str, Any]) -> None:
    if "targets" not in config:
        raise ConfigError("Config must define at least one 'targets' entry")
    targets = config["targets"]
    if not isinstance(targets, list) or len(targets) == 0:
        raise ConfigError("'targets' must be a non-empty list")
    for i, target in enumerate(targets):
        _validate_target(target, i)


def load_config(path: Optional[str] = None) -> Dict[str, Any]:
    """Load and validate a YAML config file.

    Falls back to the HOOKPIPE_CONFIG environment variable when *path* is None.

    Raises:
        ConfigError: If the file cannot be read, parsed, or fails validation.
    """
    if yaml is None:
        raise ConfigError("PyYAML is required to load configuration files")

    resolved = path or os.environ.get("HOOKPIPE_CONFIG")
    if not resolved:
        raise ConfigError(
            "No config path provided and HOOKPIPE_CONFIG env var is not set"
        )

    try:
        with open(resolved, "r", encoding="utf-8") as fh:
            raw = yaml.safe_load(fh)
    except FileNotFoundError as exc:
        raise ConfigError(f"Config file not found: {resolved}") from exc
    except yaml.YAMLError as exc:
        raise ConfigError(f"YAML parse error in {resolved}: {exc}") from exc

    if not isinstance(raw, dict):
        raise ConfigError("Config file must contain a YAML mapping at the top level")

    _validate_config(raw)
    return raw
