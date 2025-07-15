# beam_solver.py
import numpy as np
from calfem.core import assem, beam2e, beam2s, coordxtr, extract_ed, solveq


def solve_beam(geometry, element_properties, loads):
    """
    Solve the beam problem given geometry, element properties, and loads.
    """
    ndofs = geometry["ndofs"]
    nels = geometry["nels"]
    coord = np.array(geometry["coord"])
    dof = np.array(geometry["dof"])
    edof = np.array(geometry["edof"])
    bc = np.array(geometry["bc"])

    # Initialize global stiffness matrix, force vector, and distributed load
    K = np.zeros((ndofs, ndofs))
    f = np.zeros((ndofs, 1))

    # Prepare arrays for element properties and distributed loads
    ep = np.zeros((nels, 3))
    eq = np.zeros((nels, 2))

    # Apply point loads if specified
    if "P_loc" in loads and "P" in loads:
        P_locs = loads["P_loc"]
        P_values = loads["P"]
        if isinstance(P_locs, int):
            P_locs = [P_locs]
            P_values = [P_values]
        elif isinstance(P_locs, list):
            pass  # P_locs and P_values are lists
        else:
            raise TypeError("Unexpected type for P_loc. Expected int or list.")
        if len(P_locs) != len(P_values):
            raise ValueError("P_loc and P must be the same length.")
        for dof_num, P_value in zip(P_locs, P_values):
            if 0 <= dof_num < ndofs:
                f[dof_num, 0] += P_value

    # Apply moment loads if specified
    if "M_loc" in loads and "M" in loads:
        M_locs = loads["M_loc"]
        M_values = loads["M"]
        if isinstance(M_locs, int):
            M_locs = [M_locs]
            M_values = [M_values]
        elif isinstance(M_locs, list):
            pass  # M_locs and M_values are lists
        else:
            raise TypeError("Unexpected type for M_loc. Expected int or list.")
        if len(M_locs) != len(M_values):
            raise ValueError("M_loc and M must be the same length.")
        for dof_num, M_value in zip(M_locs, M_values):
            if 0 <= dof_num < ndofs:
                f[dof_num, 0] += M_value

    # Apply distributed loads if specified
    if "q_loc" in loads and "q" in loads:
        q_locs = loads["q_loc"]
        q_values = loads["q"]
        if isinstance(q_locs, int):
            q_locs = [q_locs]
            q_values = [q_values]
        elif isinstance(q_locs, list):
            pass  # q_locs and q_values are lists
        else:
            raise TypeError("Unexpected type for q_loc. Expected int or list.")
        if len(q_locs) != len(q_values):
            raise ValueError("q_loc and q must be the same length.")
        for elem_idx, q_value in zip(q_locs, q_values):
            if 0 <= elem_idx < nels:
                eq[elem_idx] += [0, q_value]
            else:
                print(f"Invalid element index {elem_idx} for distributed load.")

    # Extract element properties
    for i in range(nels):
        ep[i] = [
            element_properties[i]["material"]["E"],
            element_properties[i]["section"]["A"] * 10**-4,
            element_properties[i]["section"]["I"] * 10**-8,
        ]

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
    max_results = {"displacement": 0, "shear_force": 0, "moment": 0}

    for i in range(nels):
        es, edi, eci = beam2s(ex[i], ey[i], ep[i], ed[i], eq[i], 11)
        element_results[i] = {"es": es, "edi": edi, "eci": eci}
        current_max_displacement = np.max(np.abs(edi))
        current_max_shear = np.max(np.abs(es[1]))
        current_max_moment = np.max(np.abs(es[2]))
        max_results["displacement"] = max(max_results["displacement"], current_max_displacement)
        max_results["shear_force"] = max(max_results["shear_force"], current_max_shear)
        max_results["moment"] = max(max_results["moment"], current_max_moment)

    return a, ex, ey, element_results, max_results
