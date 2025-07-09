# src/taskgen/__init__.py
from importlib import metadata as _meta

"""Structural FEM task generator."""
__version__ = "0.1.0"
try:
    __version__ = _meta.version(__name__)
except _meta.PackageNotFoundError:
    pass
