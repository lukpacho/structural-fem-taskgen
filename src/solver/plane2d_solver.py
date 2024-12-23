import numpy as np

import calfem.core as cfc
import calfem.utils as cfu


def solve_plane2d(coords, dofs, edofs, bdofs, material_data, boundary_conditions, loads):
    """
    Solve a 2D plane stress/strain problem given a meshed geometry.

    Parameters
    ----------
    coords : ndarray (n_nodes, 2)
        Node coordinates.
    dofs : ndarray (n_nodes, 2)
        Global dof indices for each node.
    edofs : ndarray (n_elements, n_dofs_per_el)
        Element topology (each row: global DOFs).
    bdofs : dict
        Dictionary from boundary-marker => list/array of DOFs.
    material_data : dict
        { "ptype": (0=plane stress or 1=plane strain),
          "E": float,
          "nu": float,
          "t": float }
    boundary_conditions : dict
        For example:
            {
              "bc1": { "marker": 10, "value": 0.0, "dimension": 0 },
              ...
            }
    loads : dict
        For example:
            {
              "force1": { "marker": 1, "value": 100.0, "dimension": 1 },
              ...
            }

    Returns
    -------
    a : ndarray
        Displacement vector of size n_dofs x 1
    r : ndarray
        Reaction force vector of size n_dofs x 1
    es : ndarray
        Element stress array, shape (n_elements, 3) => [σx, σy, τxy]
    ed : ndarray
        Element displacement array, shape (n_elements, n_dofs_per_el)
    """

    # -- Extract material data --
    ptype = material_data['ptype']  # 1 or 2
    E = material_data['E']
    nu = material_data['nu']
    t = material_data['t']

    # Construct constitutive matrix
    ep = [ptype, t]
    D = cfc.hooke(ptype, E, nu)

    # Number of total dofs:
    n_dofs = dofs.size

    # Extract element node coords
    ex, ey = cfc.coordxtr(edofs, coords, dofs)

    # Allocate global K and f
    K = np.zeros((n_dofs, n_dofs))
    f = np.zeros((n_dofs, 1))

    # --- Assemble global stiffness ---
    for i in range(edofs.shape[0]):
        Ke = cfc.plante(ex[i, :], ey[i, :], ep, D)
        cfc.assem(edofs[i], K, Ke)

    # Apply boundary conditions
    bc = np.array([], dtype=int)
    bcVal = np.array([], dtype=float)
    for bc_key, bc_data in boundary_conditions.items():
        marker = bc_data["marker"]
        value = bc_data["value"]
        dimension = bc_data["dimension"]
        bc, bcVal = cfu.applybc(bdofs, bc, bcVal, marker, value, dimension)

    # Apply loads
    for force_key, force_data in loads.items():
        marker = force_data["marker"]
        value = force_data["value"]
        dimension = force_data["dimension"]
        cfu.applyforce(bdofs, f, marker, value, dimension)

    # --- Solve system ---
    a, r = cfc.solveq(K, f, bc, bcVal)

    # --- Compute element displacements and stresses ---
    ed = cfc.extract_eldisp(edofs, a)
    es_list = []
    for i in range(edofs.shape[0]):
        es_i, et_i = cfc.plants(ex[i, :], ey[i, :], ep, D, ed[i, :])
        es_list.append(es_i[0]) # es_i is shape (1,3) => [σx, σy, τxy]
    es = np.array(es_list)  # (n_elements, 3)

    return a, r, es, ed