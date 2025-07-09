# src/taskgen/core/config.py
from __future__ import annotations

import json
from importlib.resources import as_file, files
from pathlib import Path

from platformdirs import user_cache_dir

# ── Configs
CM_TO_IN: float = 1 / 2.54  # centimetres → inches
M_TO_CM: float = 100.0  # metres → centimetres
ANNOTATION_DISPLACEMENT_MIN = 0.01  # m
ANNOTATION_THRESHOLD = 0.01  # unitless

# ── Read‑only resources
_PACKAGE_ROOT = files("taskgen")
DATA_DIR = _PACKAGE_ROOT / "data"
with as_file(_PACKAGE_ROOT / "templates") as p:
    TEMPLATES_DIR: Path = p


def load_properties() -> dict:
    """Return the dict stored in data/properties.json (works from wheel or sdist)."""
    resource = DATA_DIR / "properties.json"
    with as_file(resource) as fp:
        return json.load(fp.open("r"))


# ── Writable directories
# Default root in user cache (e.g., ~/.cache/taskgen)
_OUTPUT_ROOT = Path(user_cache_dir("taskgen"))
for sub in ("temp", "pdfs", "results"):
    (_OUTPUT_ROOT / sub).mkdir(parents=True, exist_ok=True)

DEFAULT_OUT_ROOT = _OUTPUT_ROOT


def set_output_root(root: Path) -> None:
    """Call from CLI if the user supplies --out-root."""
    global _OUTPUT_ROOT
    _OUTPUT_ROOT = root
    for sub in ("temp", "pdfs", "results"):
        (root / sub).mkdir(parents=True, exist_ok=True)


def temp_dir() -> Path:
    return _OUTPUT_ROOT / "temp"


def pdfs_dir() -> Path:
    return _OUTPUT_ROOT / "pdfs"


def results_dir() -> Path:
    return _OUTPUT_ROOT / "results"
