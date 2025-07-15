# src/taskgen/__init__.py
from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("structural-fem-taskgen-cli")
except PackageNotFoundError:
    __version__ = "0.0.0.dev0"
