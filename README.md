[![CI](https://github.com/lukpacho/structural-fem-taskgen/actions/workflows/ci.yml/badge.svg)](https://github.com/lukpacho/structural-fem-taskgen/actions/workflows/ci.yml)
[![PyPI – latest](https://img.shields.io/pypi/v/structural-fem-taskgen-cli.svg)](https://pypi.org/project/structural-fem-taskgen-cli/)
[![Test PyPI](https://img.shields.io/badge/Test%20PyPI-β-lightgrey)](https://test.pypi.org/project/structural-fem-taskgen-cli/)
[![Docker pulls](https://img.shields.io/docker/pulls/lukpacho/taskgen)](https://hub.docker.com/r/lukpacho/taskgen)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

Generate **random or predefined** beam / plane‑stress (CST) tasks, solve them
with CalFEM and produce:

* PDF task cards (TikZ, Tectonic)
* PNG plots (internal forces, displacements, stresses)
* JSON results for auto‑grading

Powered by **NumPy**, **CALFEM**, **gmsh** & **Tectonic**; wrapped in a single Typer CLI and container image.

## Requires
* Linux (x86-64). Tested on Ubuntu 22.04/24.04 & WSL2.
* Tectonic ≥ 0.15 for local PDF generation  
`curl --proto '=https' --tlsv1.2 -fsSL https://drop-sh.fullyjustified.net \| sh`


## Install

| Tool             | Command |
|------------------|---------|
| **Stable wheel** | `pip install structural-fem-taskgen-cli` |
| **Test PyPI**    | `pip install -i https://test.pypi.org/simple structural-fem-taskgen-cli` |
| **Docker image** | `docker pull lukpacho/taskgen:latest` |


---
## Quick Use ⚡️
### CLI summary
```Bash
taskgen --help
usage: taskgen [OPTIONS] COMMAND [ARGS]...

Options:
  --out-root, -o  Output directory (default: "./out" for docker, "~/.cache/taskgen" for local Python)
  --version, -V   Print version and exit
  --help          Show this message and exit

Commands:
  beam     Generate / solve 1‑D beam problems
  plane2d  Generate / solve 2‑D plane (CST) problems
  
Args: (see docs for beam/plan2d geometries)
  --beam-version (-v)     Available options: [1, 2, 3, 4, 5, 6, 7, 8, 999]
  --plane2d-version (-v)  Available options: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
  --num (-n)              Number of simulations per beam/plane2d version
```

## Examples
### Local Python / Docker container
```bash
# Create out/ directory
mkdir out
# Generate 10 random beams of beam-version 2 with task PDFs and solutions
taskgen --out-root ./out beam random -v 2 -n 10
# Generate 5 random beam tasks of beam-versions 2, 3, 4, 5 with task PDFs and solutions
takgen --out-root ./out beam random -v 2 -v 3 -v 4 -v 5 -n 5
# Do the same for plane2d through Docker (keeps host UID/GID)
docker run --rm \
  -e HOST_UID=$(id -u) -e HOST_GID=$(id -g) \
  -v "$PWD/out:/out" \
  lukpacho/taskgen \
  plane2d random -v 2 -v 3 -v 4 -v 5 -n 5
```

---
## Develop 🛠️

```bash
git clone https://github.com/lukpacho/structural-fem-taskgen.git
cd structural-fem-taskgen

# new env with deps
python -m venv .venv && source .venv/bin/activate
pip install -e .[dev]

# one‑shot lint | type‑check | tests
ruff check .
mypy src/ tests/
pytest -q

# auto‑format before commit
pre-commit install
```

### Local smoke test
```bash
python -m build --wheel -o /tmp/dist
pipx run --spec /tmp/dist/*.whl taskgen --help
docker build -t taskgen-dev .
docker run --rm taskgen-dev --help
```

---
### Release 📦 GitHub Actions workflow 

1. Lint, type‑check, test on 3.11 & 3.12.
2. Build wheel + sdist → `pip check` → `taskgen --help`
3. Upload to Test PyPI or PyPI (**`PYPI_TARGET`** (`test`/`prod`)).
4. Build & push multi‑arch Docker images to GHCR and DockerHub.
5. Run container smoke-test (`docker run … --help`).
