# main.py
import argparse
import os
import warnings
warnings.filterwarnings("ignore", category=PendingDeprecationWarning)

# Beam imports
from src.generators.beam_generator import load_properties, save_beam_input, generate_geometry, generate_element_properties, generate_loads
from src.solver.beam_solver import solve_beam
from src.solver.beam_plotter import plot_beam_results
from src.pdf_generator.beam_pdf_generator import prepare_data_for_latex, generate_beam_pdf

# Plane2D imports
from src.solver.plane2d_solver import solve_plane2d, build_plane2d_with_predefined_mesh
from src.solver.plane2d_plotter import plot_plane2d_results, plot_predefined_mesh_with_numbering
# from src.pdf_generator.plane2d_pdf_generator import prepare_data_for_latex_plane, generate_plane_pdf


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
            data = prepare_data_for_latex(beam_version, simulation_index, geometry, element_properties, loads)
            output_filename = '_'.join([mode, beam_version, str(simulation_index), 'report'])
            generate_beam_pdf("beam_template.tex", output_filename, data)

    elif mode == 'predefined':
        simulation_index = 0
        geometry = properties[beam_version]['geometry']
        element_properties = properties[beam_version]['element_properties']
        loads = properties[beam_version]['loads']

        a, ex, ey, element_results, max_results = solve_beam(geometry, element_properties, loads)

        plot_beam_results(ex, ey, element_results, max_results, mode, beam_version)

        if generate_pdf:
            data = prepare_data_for_latex(beam_version, simulation_index, geometry, element_properties, loads)
            output_filename = '_'.join([mode, beam_version, str(simulation_index), 'report'])
            generate_beam_pdf("beam_template.tex", output_filename, data)


def run_plane_simulation(properties: dict, plane_version: str,
                         num_simulations: int = 1, mode: str = "random", generate_pdf: bool = True):
    """
    Run plane simulations and generate corresponding documentation.

    Parameters:
        properties (dict): Dictionary of properties to use.
        plane_version (str): Version of plane.
        num_simulations (int): Number of simulations to run.
        mode (str): Simulation mode (random or predefined).
        generate_pdf (bool): Whether to generate PDF documents.
    """
    if mode == 'random':
        pass
    elif mode == 'predefined':
        simulation_index = 0
        plane_data = properties[plane_version]
        el_type = plane_data['el_type']
        dofs_per_node = plane_data['dofs_per_node']
        el_size_factor = plane_data['el_size_factor']
        points = plane_data['geometry']['points']
        elements = plane_data['geometry']['elements']
        material_data = plane_data['material_data']
        boundary_conditions = plane_data['boundary_conditions']
        loads = plane_data['loads']

        coords, dofs, edofs, bdofs = build_plane2d_with_predefined_mesh(
            points, elements, boundary_conditions, loads
        )

        simulation_data = [mode, plane_version, simulation_index]
        plot_predefined_mesh_with_numbering(coords, dofs, edofs, dofs_per_node, el_type, simulation_data)

        a, r, es, ed = solve_plane2d(
            coords, dofs, edofs, bdofs,
            material_data, boundary_conditions, loads
        )


    pass


def main():
    parser = argparse.ArgumentParser(description='Run simulation(s).')
    parser.add_argument('--problem_type', type=str, choices=['beam', 'plane2d'], default='beam',
                        help='Which type of problem to solve? (beam or plane2d)')
    parser.add_argument('--mode', type=str, choices=['random', 'predefined'], default='random',
                        help='Simulation mode: random or predefined')
    parser.add_argument('--beam_version', type=list, nargs='+', default=[999],
                        help='Beam version(s) to simulate. Used if problem_type=beam.')
    parser.add_argument('--plane_version', type=list, default=[999],
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
            for version in args.plane_version:
                plane_version = f'plane{int(version[0])}'
                run_plane_simulation(
                    properties=properties,
                    plane_version=plane_version,
                    num_simulations=args.num_simulations,
                    mode=args.mode,
                    generate_pdf=args.generate_pdf,
                )
        elif args.mode == 'predefined':
            plane_number = ''.join(args.plane_version[0])
            plane_version = f'plane{int(plane_number)}'
            run_plane_simulation(
                properties=properties,
                plane_version=plane_version,
                num_simulations=args.num_simulations,
                mode=args.mode,
                generate_pdf=args.generate_pdf,
            )

if __name__ == '__main__':
    main()
