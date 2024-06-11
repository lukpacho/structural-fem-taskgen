# main.py
import os
from src.generator import load_properties, generate_geometry, generate_element_properties, generate_loads
from src.solver.beam_solver import solve_beam, plot_beam_results
from src.pdf_generator.pdf_generator import generate_beam_pdf


def run_simulation(beam_version, num_simulations):
    """
    Run beam simulations and generate corresponding documentation.

    Parameters:
    - beam_version: Version of the beam setup to simulate.
    - num_simulations: Number of simulations to perform.
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    properties_path = os.path.join(current_dir, 'data', 'properties.json')
    properties = load_properties(properties_path)

    for simulation_index in range(num_simulations):
        while True:
            # Generate data for the beam
            geometry, max_length = generate_geometry(beam_version, properties)
            element_properties = generate_element_properties(geometry, properties)
            loads = generate_loads(geometry, properties)
            # Solve beam equations and get maximum displacement
            a, ex, ey, element_results, max_results = solve_beam(geometry, element_properties, loads)


            # Check if the simulation results are within the acceptable range
            # if actual_max_displacement < max_allowed_displacement / 10:
            #     break

            plot_beam_results(ex, ey, element_results, max_results,
                              beam_version_to_simulate, simulation_index)
            break

        # Generate PDF report for the simulation
        generate_beam_pdf()


if __name__ == '__main__':
    number_of_simulations = 1
    beam_version_to_simulate = 999
    run_simulation(beam_version_to_simulate, number_of_simulations)
