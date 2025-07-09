from .config import load_properties
from .orchestrator import run_beam_simulation, run_plane2d_simulation

__all__ = ["run_beam", "run_plane2d"]


def run_beam(
    mode: str,
    versions: list[int],
    num: int,
    generate_pdf: bool,
):
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
):
    props = load_properties()[mode]
    for v in versions:
        run_plane2d_simulation(
            properties=props,
            plane2d_version=f"plane{v}",
            num_simulations=num,
            mode=mode,
            generate_pdf=generate_pdf,
        )
