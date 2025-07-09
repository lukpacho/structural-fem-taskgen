### cli.py
from pathlib import Path
from typing import List

import typer

from taskgen.core import orchestrator_adapter as core
from taskgen.core.config import DEFAULT_OUT_ROOT, set_output_root

app = typer.Typer(
    add_completion=False,
    help="Generate & solve structural FEM tasks (beam / plane2d).",
)


@app.callback()
def cli(
    out_root: Path = typer.Option(
        DEFAULT_OUT_ROOT, "--out-root", "-o", help="Root directory for output files."
    )
):
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
        help="Beam version(s). Repeat flag, e.g.  -v 2 -v 3",
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
    core.run_beam(mode, versions, num, generate_pdf=not no_pdf)


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
        help="Plane2D version(s). Repeat flag, e.g.  -v 2 -v 3",
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
    core.run_plane2d(mode, versions, num, generate_pdf=not no_pdf)


if __name__ == "__main__":
    app()
