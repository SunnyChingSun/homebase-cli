from __future__ import annotations

import json
from pathlib import Path
from typing import Any


APP_DIR = Path.home() / ".homebase"
CONTEXTS_PATH = APP_DIR / "contexts.json"
HISTORY_PATH = APP_DIR / "history.json"


def ensure_storage() -> None:
    APP_DIR.mkdir(parents=True, exist_ok=True)
    if not CONTEXTS_PATH.exists():
        write_contexts({})
    if not HISTORY_PATH.exists():
        write_history([])


def _read_json(path: Path, default: Any) -> Any:
    ensure_storage_dir_only()
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _write_json(path: Path, data: Any) -> None:
    ensure_storage_dir_only()
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def ensure_storage_dir_only() -> None:
    APP_DIR.mkdir(parents=True, exist_ok=True)


def read_contexts() -> dict[str, Any]:
    data = _read_json(CONTEXTS_PATH, {})
    if not isinstance(data, dict):
        return {}
    return data


def write_contexts(contexts: dict[str, Any]) -> None:
    _write_json(CONTEXTS_PATH, contexts)


def read_history() -> list[dict[str, Any]]:
    data = _read_json(HISTORY_PATH, [])
    if not isinstance(data, list):
        return []
    return data


def write_history(history: list[dict[str, Any]]) -> None:
    _write_json(HISTORY_PATH, history)

