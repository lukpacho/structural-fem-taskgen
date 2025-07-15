# cli.py
from __future__ import annotations

import sys
from pathlib import Path
from typing import List

import typer

from taskgen import __version__
from taskgen.core.config import DEFAULT_OUT_ROOT, set_output_root
from taskgen.core.orchestrator_adapter import run_beam, run_plane2d

if sys.version_info < (3, 11):
    sys.stderr.write("structural-fem-taskgen-cli requires Python ≥ 3.11\n")
    sys.exit(1)

app = typer.Typer(
    add_completion=False,
    help="Generate & solve structural FEM tasks (beam / plane2d).",
)


@app.callback(invoke_without_command=True)
def root_options(
    _ctx: typer.Context,
    out_root: Path = typer.Option(
        DEFAULT_OUT_ROOT, "--out-root", "-o", help="Root directory for output files."
    ),
    show_version: bool = typer.Option(
        False, "--version", "-V", help="Show version and exit.", is_eager=True
    ),
) -> None:
    if show_version:
        typer.echo(f"structural-fem-taskgen-cli v{__version__}")
        raise typer.Exit()

    set_output_root(out_root)


# ----------------------------------------------------------------------
# BEAM
# ----------------------------------------------------------------------
@app.command()
def beam(
    mode: str = typer.Argument(
        ...,
        metavar="MODE",
        help="Simulation mode: random | predefined",
    ),
    beam_version: List[int] = typer.Option(
        None,
        "--beam-version",
        "-v",
        help="Beam version(s). Repeatable flag, e.g.  -v 2 -v 3",
    ),
    num: int = typer.Option(
        1,
        "--num",
        "-n",
        help="Number of beams to generate (random mode only)",
    ),
    no_pdf: bool = typer.Option(
        False,
        "--no-pdf",
        help="Skip PDF generation (plots still saved)",
    ),
):
    """Generate / solve beam problems."""
    versions = beam_version or [999]
    run_beam(mode, versions, num, generate_pdf=not no_pdf)


# ----------------------------------------------------------------------
# PLANE 2-D
# ----------------------------------------------------------------------
@app.command()
def plane2d(
    mode: str = typer.Argument(
        ...,
        metavar="MODE",
        help="Simulation mode: random | predefined",
    ),
    plane2d_version: List[int] = typer.Option(
        None,
        "--plane2d-version",
        "-v",
        help="Plane2D version(s). Repeatable flag, e.g.  -v 2 -v 3",
    ),
    num: int = typer.Option(
        1,
        "--num",
        "-n",
        help="Number of simulations (random mode only)",
    ),
    no_pdf: bool = typer.Option(
        False,
        "--no-pdf",
        help="Skip PDF generation (plots still saved)",
    ),
):
    """Generate / solve PLANE-2D frame problems."""
    versions = plane2d_version or [999]
    run_plane2d(mode, versions, num, generate_pdf=not no_pdf)


if __name__ == "__main__":
    app()
