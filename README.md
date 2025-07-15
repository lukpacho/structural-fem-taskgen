[![CI](https://github.com/lukpacho/structural-fem-taskgen/actions/workflows/ci.yml/badge.svg)](https://github.com/lukpacho/structural-fem-taskgen/actions/workflows/ci.yml)
[![PyPI – latest](https://img.shields.io/pypi/v/structural_fem_taskgen_cli.svg)](https://pypi.org/project/structural-fem-taskgen-cli/)
[![Test PyPI](https://img.shields.io/badge/Test%20PyPI-β-lightgrey)](https://test.pypi.org/project/structural-fem-taskgen-cli/)
[![Docker pulls](https://img.shields.io/docker/pulls/lukpacho/taskgen)](https://hub.docker.com/r/lukpacho/taskgen)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

Generate **random or predefined** beam / plane‑stress (CST) tasks, solve them
with CalFEM and produce:

* PDF task cards (TikZ, Tectonic)
* PNG plots (internal forces, displacements, stresses)
* JSON results for auto‑grading

Powered by **NumPy**, **CALFEM**, **gmsh** & **Tectonic**; wrapped in a single Typer CLI and container image.

## Installation

| Tool             | Command |
|------------------|---------|
| **Stable wheel** | `pip install structural-fem-taskgen-cli` |
| **Test PyPI**    | `pip install -i https://test.pypi.org/simple structural-fem-taskgen-cli` |
| **Docker image** | `docker pull lukpacho/taskgen:latest` |


---
## Quick start using container

```bash
# Results land in ./out (created if absent)
mkdir out
docker run --rm \
  -e HOST_UID=$(id -u) -e HOST_GID=$(id -g) \
  -v "$PWD/out:/out" \
  lukpacho/taskgen \
  --out-root /out beam random -v 2 -n 2
```
