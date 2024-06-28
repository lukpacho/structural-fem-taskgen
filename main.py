# main.py
import argparse
import os
from src.generator import load_properties, save_beam_input, generate_geometry, generate_element_properties, generate_loads
from src.solver.beam_solver import solve_beam
from src.solver.beam_plotter import plot_beam_results
from src.pdf_generator.pdf_generator import generate_beam_pdf


def run_simulation(beam_version, num_simulations, mode, properties):
    """
    Run beam simulations and generate corresponding documentation.

    Parameters:
    - beam_version: Version of the beam setup to simulate.
    - num_simulations: Number of simulations to perform.
    - mode: Simulation mode.
    - properties: Properties of the beam versions, element properties, and loads
    """
    if mode == 'random':
        for simulation_index in range(num_simulations):
            while True:
                geometry, max_length = generate_geometry(beam_version, properties)
                element_properties = generate_element_properties(geometry, properties)
                loads = generate_loads(geometry, properties)
                a, ex, ey, element_results, max_results = solve_beam(geometry, element_properties, loads)

                actual_max_displacement = max_results['ed']
                max_allowed_displacement = max_length / 10

                # Check if the simulation results are within the acceptable range
                if actual_max_displacement < max_allowed_displacement / 10:
                    break

            save_beam_input(geometry, element_properties, loads, mode, beam_version, simulation_index)
            plot_beam_results(ex, ey, element_results, max_results, mode, beam_version, simulation_index)

            # Generate PDF report for the simulation
            generate_beam_pdf()

    elif mode == 'predefined':
        geometry = properties[beam_version]['geometry']
        element_properties = properties[beam_version]['element_properties']
        loads = properties[beam_version]['loads']
        # Solve beam equations and get maximum displacement
        a, ex, ey, element_results, max_results = solve_beam(geometry, element_properties, loads)

        plot_beam_results(ex, ey, element_results, max_results, mode, beam_version)

        # Generate PDF report for the simulation
        generate_beam_pdf()


def main():
    parser = argparse.ArgumentParser(description='Run beam simulation(s).')
    parser.add_argument('--mode', type=str, choices=['random', 'predefined'], default='random',
                        help='Simulation mode: random or predefined')
    parser.add_argument('--beam_version', type=int, nargs='+', default=[999], help='Beam version(s) to simulate')
    parser.add_argument('--num_simulations', type=int, default=1, help='Number of simulations to perform')

    args = parser.parse_args()

    if args.mode == 'predefined' and args.num_simulations != 1:
        raise ValueError("Multiple simulations are not allowed in predefined mode.")

    current_dir = os.path.dirname(os.path.abspath(__file__))
    properties_path = os.path.join(current_dir, 'data', 'properties.json')
    properties = load_properties(properties_path)[args.mode]

    for version in args.beam_version:
        beam_version = f'beam{version}'
        run_simulation(beam_version, args.num_simulations, args.mode, properties)


if __name__ == '__main__':
    main()
