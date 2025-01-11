# main.py
import argparse
import os
import warnings
warnings.filterwarnings("ignore", category=PendingDeprecationWarning)

# Beam imports
from src.generators.beam_generator import load_properties, save_beam_input, generate_geometry, generate_element_properties, generate_loads
from src.solver.beam_solver import solve_beam
from src.solver.beam_plotter import plot_beam_results
from src.pdf_generator.description_pdf_generator import prepare_beam_data_for_latex, generate_description_pdf

# Plane2D imports
from src.solver.plane2d_solver import (solve_plane2d, build_plane2d_with_predefined_mesh, build_plane2d_with_auto_mesh,
                                       load_plane2d_version_properties)
from src.pdf_generator.description_pdf_generator import prepare_plane2d_data_for_latex


def run_beam_simulation(properties: dict, beam_version: str,
                        num_simulations: int = 1, mode: str = "random", generate_pdf: bool = True):
    """
    Run beam simulations and generate corresponding documentation.

    Parameters:
        properties (dict): Dictionary of properties to use.
        beam_version (str): Version of beam.
        num_simulations (int): Number of simulations to run.
        mode (str): Simulation mode (random or predefined).
        generate_pdf (bool): Whether to generate PDF documents.
    """
    if mode == 'random':
        for simulation_index in range(num_simulations):
            while True:
                geometry, max_length = generate_geometry(beam_version, properties)
                element_properties = generate_element_properties(geometry, properties)
                loads = generate_loads(geometry, properties, 2, 2, 2)
                a, ex, ey, element_results, max_results = solve_beam(geometry, element_properties, loads)

                actual_max_displacement = max_results['displacement']
                max_allowed_displacement = max_length / 10

                # Check if the simulation results are within the acceptable range
                if actual_max_displacement < max_allowed_displacement / 10:
                    break

            save_beam_input(geometry, element_properties, loads, mode, beam_version, simulation_index)
            plot_beam_results(ex, ey, element_results, max_results, mode, beam_version, simulation_index)

            # Generate PDF report for the simulation
            data = prepare_beam_data_for_latex(beam_version, simulation_index, geometry, element_properties, loads)
            output_filename = '_'.join([mode, beam_version, str(simulation_index), 'report'])
            generate_description_pdf("beam_template.tex", output_filename, data)

    elif mode == 'predefined':
        simulation_index = 0
        geometry = properties[beam_version]['geometry']
        element_properties = properties[beam_version]['element_properties']
        loads = properties[beam_version]['loads']

        a, ex, ey, element_results, max_results = solve_beam(geometry, element_properties, loads)

        plot_beam_results(ex, ey, element_results, max_results, mode, beam_version)

        if generate_pdf:
            data = prepare_beam_data_for_latex(beam_version, simulation_index, geometry, element_properties, loads)
            output_filename = '_'.join([mode, beam_version, str(simulation_index), 'report'])
            generate_description_pdf("beam_template.tex", output_filename, data)


def run_plane2d_simulation(properties: dict, plane2d_version: str,
                           num_simulations: int = 1, mode: str = "random", generate_pdf: bool = True):
    """
    Run plane simulations and generate corresponding documentation.

    Parameters:
        properties (dict): Dictionary of properties to use.
        plane2d_version (str): Version of plane.
        num_simulations (int): Number of simulations to run.
        mode (str): Simulation mode (random or predefined).
        generate_pdf (bool): Whether to generate PDF documents.
    """
    if mode == 'random':

        pass
    elif mode == 'predefined':
        simulation_index = 0
        simulation_data = [mode, plane2d_version, simulation_index]

        points, elements, material_data, boundary_conditions, forces, mesh_props = (
            load_plane2d_version_properties(properties, plane2d_version))

        coords, dofs, edofs, bdofs = build_plane2d_with_predefined_mesh(
            points, elements, boundary_conditions, forces
        )

        a, r, es, ed = solve_plane2d(
            coords, dofs, edofs, bdofs,
            material_data, boundary_conditions, forces
        )

        if generate_pdf:
            data = prepare_plane2d_data_for_latex(
                plane2d_version, simulation_index, simulation_data, coords, dofs, edofs, material_data,
                boundary_conditions, forces, mesh_props
            )
            output_filename = '_'.join([mode, plane2d_version, str(simulation_index), 'description'])
            generate_description_pdf("plane2d_template.tex", output_filename, data)


def main():
    parser = argparse.ArgumentParser(description='Run simulation(s).')
    parser.add_argument('--problem_type', type=str, choices=['beam', 'plane2d'], default='beam',
                        help='Which type of problem to solve? (beam or plane2d)')
    parser.add_argument('--mode', type=str, choices=['random', 'predefined'], default='random',
                        help='Simulation mode: random or predefined')
    parser.add_argument('--beam_version', type=list, nargs='+', default=[999],
                        help='Beam version(s) to simulate. Used if problem_type=beam.')
    parser.add_argument('--plane2d_version', type=list, default=[999],
                        help='Plane version(s) to simulate. Used if problem_type=plane2d.')
    parser.add_argument('--num_simulations', type=int, default=1,
                        help='Number of simulations to perform (random mode only).')
    parser.add_argument('--generate_pdf', type=bool, choices=[True, False], default=True,
                        help='Specify if you want to generate beam pdf.')

    args = parser.parse_args()
    if args.mode == 'predefined' and args.num_simulations != 1:
        raise ValueError("Multiple simulations are not allowed in predefined mode.")

    current_dir = os.path.dirname(os.path.abspath(__file__))
    properties_path = os.path.join(current_dir, 'data', 'properties.json')
    properties = load_properties(properties_path)[args.mode]

    if args.problem_type == 'beam':
        if args.mode == 'random':
            for version in args.beam_version:
                beam_version = f'beam{int(version[0])}'
                run_beam_simulation(
                    properties=properties,
                    beam_version=beam_version,
                    num_simulations=args.num_simulations,
                    mode=args.mode,
                    generate_pdf=args.generate_pdf,
                )
        elif args.mode == 'predefined':
            beam_number = ''.join(args.beam_version[0])
            beam_version = f'beam{int(beam_number)}'
            run_beam_simulation(
                properties=properties,
                beam_version=beam_version,
                num_simulations=args.num_simulations,
                mode=args.mode,
                generate_pdf=args.generate_pdf,
            )
    elif args.problem_type == 'plane2d':
        if args.mode == 'random':
            for version in args.plane2d_version:
                plane2d_version = f'plane{int(version[0])}'
                run_plane2d_simulation(
                    properties=properties,
                    plane2d_version=plane2d_version,
                    num_simulations=args.num_simulations,
                    mode=args.mode,
                    generate_pdf=args.generate_pdf,
                )
        elif args.mode == 'predefined':
            plane2d_number = args.plane2d_version[0]
            plane2d_version = f'plane{int(plane2d_number)}'
            run_plane2d_simulation(
                properties=properties,
                plane2d_version=plane2d_version,
                num_simulations=args.num_simulations,
                mode=args.mode,
                generate_pdf=args.generate_pdf,
            )

if __name__ == '__main__':
    main()
