import os
import numpy as np
import matplotlib.pyplot as plt
from calfem.core import *
from calfem.vis_mpl import *


def solve_beam(geometry, element_properties, loads):
    """
    Solve the beam problem given geometry, element properties, and loads.
    """
    ndofs = geometry['ndofs']
    nels = geometry['nels']
    coord = geometry['coord']
    dof = geometry['dof']
    edof = geometry['edof']
    bc = geometry['bc']

    # Initialize global stiffness matrix, force vector, and distributed load
    K = np.zeros((ndofs, ndofs))
    f = np.zeros((ndofs, 1))

    # Prepare arrays for element properties and distributed loads
    ep = np.zeros((nels, 2))
    eq = np.zeros((nels, 1))

    # Apply point loads and moments if they are specified
    if 'P_loc' in loads and 'P' in loads:
        if 0 <= loads['P_loc'] < ndofs:
            f[loads['P_loc'], 0] += loads['P']
    if 'M_loc' in loads and 'M' in loads:
        if 0 <= loads['M_loc'] < ndofs:
            f[loads['M_loc'], 0] += loads['M']

    # Apply distributed load if specified
    if 'q_loc' in loads and 'q' in loads:
        if isinstance(loads['q_loc'], int):
            if 0 <= loads['q_loc'] < nels:
                eq[loads['q_loc']] += loads['q']
        elif isinstance(loads['q_loc'], list):
            if all(0 < q_loc < nels for q_loc in loads['q_loc']):
                eq[loads['q_loc']] += loads['q']
        else:
            raise TypeError('Unexpected type for q_loc. Expected int or list.')

    # Extract element properties
    for i in range(nels):
        ep[i] = [element_properties[i]['material']['E'],
                 element_properties[i]['section']['I']*10**-8]

    # Extract element coordinates
    ex, ey = coordxtr(edof, coord, dof, 2)

    # Assemble system
    for i in range(nels):
        Ke, fe = beam1e(ex[i], ep[i], eq[i])
        assem(edof[i], K, Ke, f, fe)

    # Solve system
    a, r = solveq(K, f, bc)

    # Post-processing to get element displacements and forces
    ed = extract_ed(edof, a)
    element_results = {}
    max_results = {'ed': 0}

    for i in range(nels):
        es, edi, eci = beam1s(ex[i], ep[i], ed[i], eq[i], 11)
        element_results[i] = {'es': es, 'edi': edi, 'eci': eci}
        current_max_displacement = np.max(np.abs(edi))
        max_results['ed'] = max(max_results['ed'], current_max_displacement)

    return a, ex, ey, element_results, max_results


def plot_beam_results(ex, ey, element_results, max_results,
                      beam_version_to_simulate, simulation_index):
    plt.rcParams.update({'font.size': 9})
    # Define offsets
    offset_x = ex.max()/20
    offset_y = 2
    limit_x = [-offset_x, ex.max()+offset_x]
    limit_y = [-offset_y, ey.max()+offset_y]

    fig, axs = plt.subplots(3, 1, figsize=(6, 8))

    # Plot displacements
    axs[0].set_title('Displacements, cm')
    plot_beam_displacements(axs[0], ex, ey, element_results, max_results,
                            limit_x, limit_y)

    # Plot shear forces
    # axs[1].set_title('Shear Forces')
    # plot_beam_shear_forces(axs[1], 'T', ex, ey, results, limits)

    # Plot moments
    # axs[2].set_title('Moments')
    # plot_beam_moments(axs[2], 'M', ex, ey, results, limits)

    # Save the figures
    plt.tight_layout()
    current_dir = os.path.dirname(os.path.abspath(__file__))
    results_name = f'{beam_version_to_simulate}_{simulation_index}_results'
    results_path = os.path.join(current_dir, '..', 'data', 'results', results_name)
    plt.savefig(results_path + '.pdf')
    plt.savefig(results_path + '.png', dpi=1200)
    plt.show()


def plot_beam_displacements(ax, ex, ey, element_results, max_results,
                            limit_x, limit_y):
    ax.set_xlim(limit_x)
    ax.set_ylim(limit_y)
    ax.axis('off')
    # eldraw2(ex, ey, [2, 1, 0])  # [linetype linecolor nodemark]
    scale_factor = scalfact2(ex, ey, max_results['ed'], 0.3)

    for i, result in element_results.items():
        edi = result['edi']
        eldisp2(ex[i], ey[i], edi, [1, 1, 1], scale_factor)


def plot_results(geometry, results):
    """
    Plot the results of the beam analysis.
    """
    plt.figure()
    for i, res in results.items():
        xi = np.cumsum([0] + geometry['L'])[i] + res['eci']
        plt.plot(xi, res['edi'], label=f'Element {i+1}')
    plt.legend()
    plt.title('Beam Displacements')
    plt.xlabel('X Coordinate')
    plt.ylabel('Displacement')
    plt.show()

# Example usage:
# Assuming geometry, properties, loads are dictionaries prepared from generator.py
# results = solve_beam(geometry, properties, loads)
# plot_results(geometry, results)
