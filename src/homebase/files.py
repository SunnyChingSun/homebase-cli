from __future__ import annotations

import shutil
from datetime import date
from pathlib import Path
from typing import Optional, Tuple, Union

from homebase.utils import expand_path


def workspace_folder(context: dict) -> Path:
    return expand_path(context["folder"])


def relative_to_workspace(path: Path, base: Path) -> str:
    try:
        return str(path.relative_to(base))
    except ValueError:
        return str(path)


def build_target_path(
    context: dict,
    source: Union[str, Path],
    subfolder: Optional[str] = None,
    new_name: Optional[str] = None,
) -> Tuple[Path, Path, str]:
    source_path = expand_path(source)
    base = workspace_folder(context)
    target_dir = base / subfolder if subfolder else base
    target_name = new_name if new_name else source_path.name
    target_path = target_dir / target_name
    relative_path = relative_to_workspace(target_path, base)
    return source_path, target_path, relative_path


def move_into_workspace(source_path: Path, target_path: Path) -> None:
    if not source_path.exists():
        raise FileNotFoundError(f"Source file does not exist: {source_path}")
    if target_path.exists():
        raise FileExistsError(f"Target already exists: {target_path}")
    target_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(source_path), str(target_path))


def record_file(context: dict, relative_path: str) -> None:
    files = context.setdefault("files", [])
    if not any(record.get("path") == relative_path for record in files):
        files.append({"path": relative_path, "added_at": date.today().isoformat()})


def remove_file_record(context: dict, relative_path: str) -> None:
    files = context.setdefault("files", [])
    context["files"] = [record for record in files if record.get("path") != relative_path]
