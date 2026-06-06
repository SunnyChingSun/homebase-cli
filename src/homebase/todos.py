from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Union

from homebase.files import relative_to_workspace, workspace_folder


def next_todo_id(context: dict) -> int:
    todos = context.setdefault("todos", [])
    if not todos:
        return 1
    return max(int(todo.get("id", 0)) for todo in todos) + 1


def resource_for_path(context: dict, path: Union[str, Path]) -> Dict[str, str]:
    base = workspace_folder(context)
    raw_path = Path(path).expanduser()
    absolute_path = raw_path if raw_path.is_absolute() else base / raw_path
    resource_type = "folder" if absolute_path.exists() and absolute_path.is_dir() else "file"
    resource_path = relative_to_workspace(absolute_path.resolve(), base)
    return {"type": resource_type, "path": resource_path}


def add_todo(
    context: dict,
    text: str,
    due: Optional[str] = None,
    resources: Optional[List[Dict[str, str]]] = None,
) -> dict:
    todo = {
        "id": next_todo_id(context),
        "text": text,
        "due": due,
        "done": False,
        "resources": resources or [],
    }
    context.setdefault("todos", []).append(todo)
    return todo


def find_todo(context: dict, todo_id: int) -> Optional[dict]:
    for todo in context.get("todos", []):
        if int(todo.get("id", 0)) == todo_id:
            return todo
    return None
