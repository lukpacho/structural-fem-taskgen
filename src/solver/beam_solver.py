import os
import numpy as np
import matplotlib.pyplot as plt
from calfem.core import *


def solve_beam(geometry, element_properties, loads):
    """
    Solve the beam problem given geometry, element properties, and loads.
    """
    ndofs = geometry['ndofs']
    nels = geometry['nels']
    coord = np.array(geometry['coord'])
    dof = np.array(geometry['dof'])
    edof = np.array(geometry['edof'])
    bc = np.array(geometry['bc'])

    # Initialize global stiffness matrix, force vector, and distributed load
    K = np.zeros((ndofs, ndofs))
    f = np.zeros((ndofs, 1))

    # Prepare arrays for element properties and distributed loads
    ep = np.zeros((nels, 3))
    eq = np.zeros((nels, 2))

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
                eq[loads['q_loc']] += [0, loads['q']]
        elif isinstance(loads['q_loc'], list):
            if all(0 < q_loc < nels for q_loc in loads['q_loc']):
                for q_loc, q in zip(loads['q_loc'], loads['q']):
                    eq[q_loc] += [0, q]
        else:
            raise TypeError('Unexpected type for q_loc. Expected int or list.')

    # Extract element properties
    for i in range(nels):
        ep[i] = [element_properties[i]['material']['E'],
                 element_properties[i]['section']['A']*10**-4,
                 element_properties[i]['section']['I']*10**-8]

    # Extract element coordinates
    ex, ey = coordxtr(edof, coord, dof, 2)

    # Assemble system
    for i in range(nels):
        Ke, fe = beam2e(ex[i], ey[i], ep[i], eq[i])
        assem(edof[i], K, Ke, f, fe)

    # Solve system
    a, r = solveq(K, f, bc)

    # Post-processing to get element displacements and forces
    ed = extract_ed(edof, a)
    element_results = {}
    max_results = {'displacement': 0, 'shear_force': 0, 'moment': 0}

    for i in range(nels):
        es, edi, eci = beam2s(ex[i], ey[i], ep[i], ed[i], eq[i], 11)
        element_results[i] = {'es': es, 'edi': edi, 'eci': eci}
        current_max_displacement = np.max(np.abs(edi))
        current_max_shear = np.max(np.abs(es[1]))
        current_max_moment = np.max(np.abs(es[2]))
        max_results['displacement'] = max(max_results['displacement'], current_max_displacement)
        max_results['shear_force'] = max(max_results['shear_force'], current_max_shear)
        max_results['moment'] = max(max_results['moment'], current_max_moment)

    return a, ex, ey, element_results, max_results


