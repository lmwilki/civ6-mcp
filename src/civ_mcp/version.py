"""Version and git metadata — computed once at import time."""

import importlib.metadata
import subprocess
from pathlib import Path


def _get_version() -> str:
    try:
        return importlib.metadata.version("civ-mcp")
    except importlib.metadata.PackageNotFoundError:
        pass
    # Fallback: read from pyproject.toml (uv run doesn't install metadata)
    pyproject = Path(__file__).resolve().parent.parent.parent / "pyproject.toml"
    if pyproject.exists():
        for line in pyproject.read_text().splitlines():
            if line.strip().startswith("version =") or line.strip().startswith("version="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return "0.0.0-dev"


def _get_git_sha() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except Exception:
        return ""


VERSION = _get_version()
GIT_SHA = _get_git_sha()
