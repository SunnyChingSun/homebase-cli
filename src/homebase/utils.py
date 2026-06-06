from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Union


def expand_path(path: Union[str, Path]) -> Path:
    return Path(path).expanduser().resolve()


def open_path(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Path does not exist: {path}")

    if sys.platform == "darwin":
        subprocess.run(["open", str(path)], check=False)
    elif sys.platform.startswith("linux"):
        subprocess.run(["xdg-open", str(path)], check=False)
    elif sys.platform.startswith("win"):
        os.startfile(path)  # type: ignore[attr-defined]
    else:
        raise RuntimeError("Unsupported operating system")
