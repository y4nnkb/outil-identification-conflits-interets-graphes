import os
from pathlib import Path
from typing import Any

import yaml


def load_yaml(path: str | Path) -> dict[str, Any]:
    with open(path, encoding="utf-8") as file:
        raw = file.read()
    for key, value in os.environ.items():
        raw = raw.replace("${" + key + "}", value)
    return yaml.safe_load(raw) or {}


def load_generation_config(path: str | Path) -> dict[str, Any]:
    return load_yaml(path)


def load_scoring_config(path: str | Path) -> dict[str, Any]:
    return load_yaml(path)


def load_neo4j_config(path: str | Path) -> dict[str, Any]:
    return load_yaml(path)
