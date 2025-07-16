# config.py
from __future__ import annotations

import json
import os
from importlib.resources import as_file, files
from pathlib import Path

# Configs & constants
CM_TO_IN: float = 1 / 2.54  # centimetres → inches
M_TO_CM: float = 100.0  # metres → centimetres
ANNOTATION_DISPLACEMENT_MIN = 0.01  # m
ANNOTATION_THRESHOLD = 0.01  # unitless

# Read-only package resources
_PACKAGE_ROOT = files("taskgen")
DATA_DIR = _PACKAGE_ROOT / "data"
with as_file(_PACKAGE_ROOT / "templates") as p:
    TEMPLATES_DIR: Path = p


def load_properties() -> dict:
    """Return the dict stored in *data/properties.json* (works from wheel or sdist)."""
    resource = DATA_DIR / "properties.json"
    with as_file(resource) as fp:
        return json.load(fp.open("r"))


# Writable cache tree priority (highest first):
#   1. $TASKGEN_CACHE_DIR – set by the entry-point to /out/.taskgen-cache
#   2. $XDG_CACHE_HOME
#   3. $HOME/.cache
#   4. /tmp/taskgen
#
def _choose_cache_root() -> Path:
    for candidate in (
        os.environ.get("TASKGEN_CACHE_DIR"),
        os.environ.get("XDG_CACHE_HOME"),
        Path.home() / ".cache" if os.environ.get("HOME") else None,
    ):
        if not candidate:
            continue
        try:
            p = Path(candidate).expanduser()
            p.mkdir(parents=True, exist_ok=True)
            return p
        except PermissionError:
            pass  # try next candidate
    # final fallback – guaranteed to work in a container
    return Path("/tmp/taskgen")


DEFAULT_OUT_ROOT = _choose_cache_root() / "taskgen"
for _sub in ("temp", "pdfs", "results"):
    (DEFAULT_OUT_ROOT / _sub).mkdir(parents=True, exist_ok=True)


def set_output_root(root: Path) -> None:
    """Override the auto-chosen cache root (used by the *--out-root* CLI flag)."""
    global DEFAULT_OUT_ROOT
    root.expanduser().resolve()
    DEFAULT_OUT_ROOT = root
    for _sub in ("temp", "pdfs", "results"):
        (root / _sub).mkdir(parents=True, exist_ok=True)


def temp_dir() -> Path:
    return DEFAULT_OUT_ROOT / "temp"


def pdfs_dir() -> Path:
    return DEFAULT_OUT_ROOT / "pdfs"


def results_dir() -> Path:
    return DEFAULT_OUT_ROOT / "results"
