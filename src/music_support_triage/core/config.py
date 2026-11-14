"""Configuration loading helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[3]


def load_yaml(path: Path) -> dict[str, Any]:
    """Load a YAML config file."""
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"Config must be a mapping: {path}")
    return data


def resolve_path(value: str | Path | None) -> Path | None:
    """Resolve a config path relative to the repository root."""
    if value is None:
        return None
    path = Path(value)
    return path if path.is_absolute() else PROJECT_ROOT / path


def load_data_config(path: Path) -> dict[str, Any]:
    """Load the data config and resolve its path entries."""
    config = load_yaml(path)
    paths = config.get("paths", {})
    resolved: dict[str, Any] = {}
    for key, value in paths.items():
        resolved[key] = resolve_path(value)
    config["paths"] = resolved
    return config
