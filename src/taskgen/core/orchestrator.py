# orchestrator.py
import argparse
import warnings

# Beam imports
from .beam_generator import (
    generate_element_properties,
    generate_geometry,
    generate_loads,
    save_beam_input,
)
from .beam_plotter import plot_beam_results
from .beam_solver import solve_beam
from .config import load_properties
from .description_pdf_generator import (
    generate_description_pdf,
    prepare_beam_data_for_latex,
    prepare_plane2d_data_for_latex,
)
from .plane2d_generator import generate_plane2d_input_random
from .plane2d_plotter import plot_plane2d_displacement, plot_plane2d_stresses

# Plane2D imports
from .plane2d_solver import (
    build_plane2d_with_auto_mesh,
    build_plane2d_with_predefined_mesh,
    edofs_to_enodes,
    find_displacement_at_predefined_nodes_in_auto_mesh,
    load_plane2d_configuration,
    save_plane2d_input_and_results,
    solve_plane2d,
)

warnings.filterwarnings("ignore", category=PendingDeprecationWarning)


def run_beam_simulation(
    properties: dict,
    beam_version: str,
    num_simulations: int = 1,
    mode: str = "random",
    generate_pdf: bool = True,
):
    """
    Run beam simulations and generate corresponding documentation.

    Parameters:
        properties (dict): Dictionary of properties to use.
        beam_version (str): Version of beam.
        num_simulations (int): Number of simulations to run.
        mode (str): Simulation mode (random or predefined).
        generate_pdf (bool): Whether to generate PDF documents.
    """
    if mode == "random":
        for simulation_index in range(num_simulations):
            while True:
                geometry, max_length = generate_geometry(beam_version, properties)
                element_properties = generate_element_properties(geometry, properties)
                loads = generate_loads(geometry, properties, 2, 2, 2)
                a, ex, ey, element_results, max_results = solve_beam(
                    geometry, element_properties, loads
                )

                actual_max_displacement = max_results["displacement"]
                max_allowed_displacement = max_length / 10

                # Check if the simulation results are within the acceptable range
                if actual_max_displacement < max_allowed_displacement / 10:
                    break

            save_beam_input(
                geometry,
                element_properties,
                loads,
                mode,
                beam_version,
                simulation_index,
            )
            plot_beam_results(
                ex,
                ey,
                element_results,
                max_results,
                mode,
                beam_version,
                simulation_index,
            )

            # Generate PDF report for the simulation
            data = prepare_beam_data_for_latex(
                beam_version, simulation_index, geometry, element_properties, loads
            )
            output_filename = "_".join([mode, beam_version, str(simulation_index), "report"])
            generate_description_pdf("beam_template.tex", output_filename, data)

    elif mode == "predefined":
        simulation_index = 0
        geometry = properties[beam_version]["geometry"]
        element_properties = properties[beam_version]["element_properties"]
        loads = properties[beam_version]["loads"]

        a, ex, ey, element_results, max_results = solve_beam(geometry, element_properties, loads)

        plot_beam_results(ex, ey, element_results, max_results, mode, beam_version)

        if generate_pdf:
            data = prepare_beam_data_for_latex(
                beam_version, simulation_index, geometry, element_properties, loads
            )
            output_filename = "_".join([mode, beam_version, str(simulation_index), "report"])
            generate_description_pdf("beam_template.tex", output_filename, data)


def run_plane2d_simulation(
    properties: dict,
    plane2d_version: str,
    num_simulations: int = 1,
    mode: str = "random",
    generate_pdf: bool = True,
):
    """
    Run plane simulations and generate corresponding documentation.

    Parameters:
        properties (dict): Dictionary of properties to use.
        plane2d_version (str): Version of plane.
        num_simulations (int): Number of simulations to run.
        mode (str): Simulation mode (random or predefined).
        generate_pdf (bool): Whether to generate PDF documents.
    """
    if mode == "random":
        for simulation_index in range(num_simulations):
            simulation_data = [mode, plane2d_version, simulation_index]
            points, elements, material_data, boundary_conditions, forces, mesh_props = (
                generate_plane2d_input_random(properties, plane2d_version)
            )

            coords, dofs, edofs, bdofs = build_plane2d_with_predefined_mesh(
                points, elements, boundary_conditions, forces
            )

            a, r, es, ed, result_summary = solve_plane2d(
                coords, dofs, edofs, bdofs, material_data, boundary_conditions, forces
            )

            for stress in ["sx", "sy"]:
                plot_plane2d_stresses(
                    coords=coords,
                    edofs=edofs,
                    dofs_per_node=mesh_props["dofs_per_node"],
                    el_type=mesh_props["el_type"],
                    es=es,
                    component=stress,
                    sim_data=simulation_data,
                    mesh_name="predef",
                )
            element_nodes = edofs_to_enodes(edofs, dofs)
            for comp in ["ux", "uy"]:
                plot_plane2d_displacement(
                    coords=coords,
                    dofs=dofs,
                    element_nodes=element_nodes,
                    a=a,
                    dofs_per_node=mesh_props["dofs_per_node"],
                    el_type=mesh_props["el_type"],
                    component=comp,
                    sim_data=simulation_data,
                    mesh_name="predef",
                )

            coords_auto, dofs_auto, edofs_auto, bdofs_auto = build_plane2d_with_auto_mesh(
                points, boundary_conditions, forces, mesh_props
            )

            a_auto, r_auto, es_auto, ed_auto, result_summary_auto = solve_plane2d(
                coords_auto,
                dofs_auto,
                edofs_auto,
                bdofs_auto,
                material_data,
                boundary_conditions,
                forces,
            )

            for stress in ["sx", "sy"]:
                plot_plane2d_stresses(
                    coords=coords_auto,
                    edofs=edofs_auto,
                    dofs_per_node=mesh_props["dofs_per_node"],
                    el_type=mesh_props["el_type"],
                    es=es_auto,
                    component=stress,
                    sim_data=simulation_data,
                    mesh_name="auto",
                )
            element_nodes_auto = edofs_to_enodes(edofs_auto, dofs_auto)
            for comp in ["ux", "uy"]:
                plot_plane2d_displacement(
                    coords=coords_auto,
                    dofs=dofs_auto,
                    element_nodes=element_nodes_auto,
                    a=a_auto,
                    dofs_per_node=mesh_props["dofs_per_node"],
                    el_type=mesh_props["el_type"],
                    component=comp,
                    sim_data=simulation_data,
                    mesh_name="auto",
                )

            automesh_corresponding_displacements = (
                find_displacement_at_predefined_nodes_in_auto_mesh(
                    coords,
                    result_summary,
                    coords_auto,
                    dofs_auto,
                    a_auto,
                )
            )

            data_to_save = {
                "result_summary": result_summary,
                "automesh_corresponding_displacements": automesh_corresponding_displacements,
                "result_summary_auto": result_summary_auto,
                "points": points,
                "elements": elements,
                "material_data": material_data,
                "boundary_conditions": boundary_conditions,
                "forces": forces,
                "mesh_props": mesh_props,
                "coords": coords.tolist(),
                "dofs": dofs.tolist(),
                "edofs": edofs.tolist(),
                "bdofs": bdofs,
                "a": a.tolist(),
            }
            save_plane2d_input_and_results(simulation_data, data_to_save)

            if generate_pdf:
                data = prepare_plane2d_data_for_latex(
                    plane2d_version,
                    simulation_index,
                    simulation_data,
                    coords,
                    dofs,
                    edofs,
                    material_data,
                    boundary_conditions,
                    forces,
                    mesh_props,
                    result_summary,
                )
                output_filename = "_".join(
                    [mode, plane2d_version, str(simulation_index), "description"]
                )
                generate_description_pdf("plane2d_template.tex", output_filename, data)

    elif mode == "predefined":
        simulation_index = 0
        simulation_data = [mode, plane2d_version, simulation_index]

        points, elements, material_data, boundary_conditions, forces, mesh_props = (
            load_plane2d_configuration(properties, plane2d_version, mode)
        )

        coords, dofs, edofs, bdofs = build_plane2d_with_predefined_mesh(
            points, elements, boundary_conditions, forces
        )

        a, r, es, ed, result_summary = solve_plane2d(
            coords, dofs, edofs, bdofs, material_data, boundary_conditions, forces
        )

        coords_auto, dofs_auto, edofs_auto, bdofs_auto = build_plane2d_with_auto_mesh(
            points, boundary_conditions, forces, mesh_props
        )

        a_auto, r_auto, es_auto, ed_auto, result_summary_auto = solve_plane2d(
            coords_auto,
            dofs_auto,
            edofs_auto,
            bdofs_auto,
            material_data,
            boundary_conditions,
            forces,
        )

        automesh_corresponding_displacements = find_displacement_at_predefined_nodes_in_auto_mesh(
            coords,
            result_summary,
            coords_auto,
            dofs_auto,
            a_auto,
        )

        data_to_save = {
            "result_summary": result_summary,
            "automesh_corresponding_displacements": automesh_corresponding_displacements,
            "points": points,
            "elements": elements,
            "material_data": material_data,
            "boundary_conditions": boundary_conditions,
            "forces": forces,
            "mesh_props": mesh_props,
            "coords": coords.tolist(),
            "dofs": dofs.tolist(),
            "edofs": edofs.tolist(),
            "bdofs": bdofs,
            "a": a.tolist(),
            "r": r.tolist(),
        }
        save_plane2d_input_and_results(simulation_data, data_to_save)

        if generate_pdf:
            data = prepare_plane2d_data_for_latex(
                plane2d_version,
                simulation_index,
                simulation_data,
                coords,
                dofs,
                edofs,
                material_data,
                boundary_conditions,
                forces,
                mesh_props,
                result_summary,
            )
            output_filename = "_".join(
                [mode, plane2d_version, str(simulation_index), "description"]
            )
            generate_description_pdf("plane2d_template.tex", output_filename, data)


def main():
    parser = argparse.ArgumentParser(description="Run simulation(s).")
    parser.add_argument(
        "--problem_type",
        type=str,
        choices=["beam", "plane2d"],
        default="beam",
        help="Which type of problem to solve? (beam or plane2d)",
    )
    parser.add_argument(
        "--mode",
        type=str,
        choices=["random", "predefined"],
        default="random",
        help="Simulation mode: random or predefined",
    )
    parser.add_argument(
        "--beam_version",
        type=list,
        nargs="+",
        default=[999],
        help="Beam version(s) to simulate. Used if problem_type=beam.",
    )
    parser.add_argument(
        "--plane2d_version",
        type=int,
        nargs="+",
        default=[999],
        help="Plane version(s) to simulate. Used if problem_type=plane2d.",
    )
    parser.add_argument(
        "--num_simulations",
        type=int,
        default=1,
        help="Number of simulations to perform (random mode only).",
    )
    parser.add_argument(
        "--generate_pdf",
        type=bool,
        choices=[True, False],
        default=True,
        help="Specify if you want to generate beam pdf.",
    )

    args = parser.parse_args()
    if args.mode == "predefined" and args.num_simulations != 1:
        raise ValueError("Multiple simulations are not allowed in predefined mode.")

    properties = load_properties()[args.mode]

    if args.problem_type == "beam":
        if args.mode == "random":
            for version in args.beam_version:
                beam_version = f"beam{int(version[0])}"
                run_beam_simulation(
                    properties=properties,
                    beam_version=beam_version,
                    num_simulations=args.num_simulations,
                    mode=args.mode,
                    generate_pdf=args.generate_pdf,
                )
        elif args.mode == "predefined":
            beam_number = "".join(args.beam_version[0])
            beam_version = f"beam{int(beam_number)}"
            run_beam_simulation(
                properties=properties,
                beam_version=beam_version,
                num_simulations=args.num_simulations,
                mode=args.mode,
                generate_pdf=args.generate_pdf,
            )
    elif args.problem_type == "plane2d":
        if args.mode == "random":
            for version in args.plane2d_version:
                plane2d_version = f"plane{int(version)}"
                num_simulations = int(args.num_simulations)
                mode = str(args.mode)
                generate_pdf = bool(args.generate_pdf)
                run_plane2d_simulation(
                    properties=properties,
                    plane2d_version=plane2d_version,
                    num_simulations=num_simulations,
                    mode=mode,
                    generate_pdf=generate_pdf,
                )
        elif args.mode == "predefined":
            plane2d_number = args.plane2d_version[0]
            plane2d_version = f"plane{int(plane2d_number)}"
            run_plane2d_simulation(
                properties=properties,
                plane2d_version=plane2d_version,
                num_simulations=args.num_simulations,
                mode=args.mode,
                generate_pdf=args.generate_pdf,
            )
