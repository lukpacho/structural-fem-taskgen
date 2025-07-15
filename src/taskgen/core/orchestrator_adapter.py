# orchestrator_adapter.py
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable

from .config import load_properties

__all__ = ["run_beam", "run_plane2d"]


if TYPE_CHECKING:
    run_beam_simulation: Callable[..., Any]
    run_plane2d_simulation: Callable[..., Any]


def _load_runtime():
    """Import heavy modules on demand."""
    global run_beam_simulation, run_plane2d_simulation
    from .orchestrator import (
        run_beam_simulation,
        run_plane2d_simulation,
    )


def run_beam(
    mode: str,
    versions: list[int],
    num: int,
    generate_pdf: bool,
) -> None:
    _load_runtime()
    props = load_properties()[mode]
    for v in versions:
        run_beam_simulation(
            properties=props,
            beam_version=f"beam{v}",
            num_simulations=num,
            mode=mode,
            generate_pdf=generate_pdf,
        )


def run_plane2d(
    mode: str,
    versions: list[int],
    num: int,
    generate_pdf: bool,
) -> None:
    _load_runtime()
    props = load_properties()[mode]
    for v in versions:
        run_plane2d_simulation(
            properties=props,
            plane2d_version=f"plane{v}",
            num_simulations=num,
            mode=mode,
            generate_pdf=generate_pdf,
        )
