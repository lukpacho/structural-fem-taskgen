# plane2d_solver.py
import itertools
import json
import os

# CalFEM for Python
import calfem.core as cfc
import calfem.geometry as cfg
import calfem.mesh as cfm
import calfem.utils as cfu
import numpy as np

from .config import results_dir


def solve_plane2d(coords, dofs, edofs, bdofs, material_data, boundary_conditions, forces):
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
    forces : dict
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
    result_summary: dict
        {
           'max_u_val': float,
           'max_u_node': int,
           'max_v_val': float,
           'max_v_node': int,
           'max_sx_val': float,
           'max_sx_elem': int,
           'max_sy_val': float,
           'max_sy_elem': int
         }
    """

    # -- Extract material data --
    ptype = material_data["ptype"]  # 1 or 2
    E = material_data["E"]
    nu = material_data["nu"]
    t = material_data["t"]

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
    for force_key, force_data in forces.items():
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
        es_list.append(es_i[0])  # es_i is shape (1,3) => [σx, σy, τxy]
    es = np.array(es_list)  # (n_elements, 3)

    # 1) find max abs horizontal/vertical displacement
    # "a" is shape (n_dofs,1). Node i => dofs[ i,0 ] => a-index => a[...] for x, dofs[i,1] => a[...] for y
    # We'll parse
    # Example: node i => x-dof => dofs[i,0]-1 => index in a
    #           node i => y-dof => dofs[i,1]-1 => index in a
    # We'll track max absolute
    max_u_val = 0.0
    max_u_node = 1
    max_v_val = 0.0
    max_v_node = 1
    for i_node in range(coords.shape[0]):
        # x dof
        a_index_x = dofs[i_node, 0] - 1
        a_index_y = dofs[i_node, 1] - 1
        ux = a[a_index_x, 0]
        vy = a[a_index_y, 0]
        if abs(ux) > abs(max_u_val):
            max_u_val = ux
            max_u_node = i_node + 1  # 1-based node index
        if abs(vy) > abs(max_v_val):
            max_v_val = vy
            max_v_node = i_node + 1

    # 2) find max abs sigma_x & sigma_y
    # es[:,0] => sigma_x, es[:,1]=>sigma_y
    # track element indices as well
    max_sx_val = 0.0
    max_sx_elem = 1
    max_sy_val = 0.0
    max_sy_elem = 1
    for i_el in range(es.shape[0]):
        sx = es[i_el, 0]
        sy = es[i_el, 1]
        if abs(sx) > abs(max_sx_val):
            max_sx_val = sx
            max_sx_elem = i_el + 1  # 1-based
        if abs(sy) > abs(max_sy_val):
            max_sy_val = sy
            max_sy_elem = i_el + 1

    result_summary = {
        "max_u_val": float(max_u_val),
        "max_u_node": max_u_node,
        "max_v_val": float(max_v_val),
        "max_v_node": max_v_node,
        "max_sx_val": float(max_sx_val),
        "max_sx_elem": max_sx_elem,
        "max_sy_val": float(max_sy_val),
        "max_sy_elem": max_sy_elem,
        "nnodes": coords.shape[0],
        "nels": edofs.shape[0],
    }

    return a, r, es, ed, result_summary


def build_plane2d_with_predefined_mesh(
    points: list, elements: list, boundary_conditions: dict, forces: dict
):
    """
    Build a plane stress/strain problem given a meshed geometry.
    """
    # --------------------------------------------
    # BUILD PREDEFINED MESH COORD & EDOF ARRAYS
    # --------------------------------------------
    coords = np.array(points)
    n_nodes = len(coords)

    # We'll define dofs for each node as (2i+1, 2i+2) => 1-based DOF indices
    dofs = np.array([[2 * node + 1, 2 * node + 2] for node in range(n_nodes)], dtype=int)

    # Build edofs array from the elements
    edofs_list = []
    for elem in elements:
        n1, n2, n3 = (elem[0] - 1, elem[1] - 1, elem[2] - 1)
        edofs_list.append([*dofs[n1], *dofs[n2], *dofs[n3]])
    edofs = np.array(edofs_list, dtype="int32")

    # Build bdofs from boundary_conditions & loads
    bdofs = {}
    import itertools

    # Boundary conditions
    for _, bc_data in boundary_conditions.items():
        marker = bc_data["marker"]
        dofs_of_points = []
        for pt in bc_data["points"]:
            point_id = pt - 1  # bc_data["points"] node IDs => 1-based
            dofs_of_points.append(dofs[point_id].tolist())
        bdofs[int(marker)] = list(itertools.chain(*dofs_of_points))

    # Loads
    for _, force_data in forces.items():
        marker = force_data["marker"]
        point_id = force_data["point"] - 1  # 0-based
        bdofs[int(marker)] = dofs[point_id].tolist()

    return coords, dofs, edofs, bdofs


def build_plane2d_with_auto_mesh(
    points: list, boundary_conditions: dict, forces: dict, mesh_props: dict
):
    g = cfg.geometry()

    for node_id, (x, y) in enumerate(points):
        g.point([x, y], marker=node_id + 1)  # 1-based marked

    n_points_geom = len(g.points)

    # Build splines in a loop => closed loop
    for i in range(n_points_geom):
        start_node = i
        end_node = (i + 1) % n_points_geom
        g.spline(
            [start_node, end_node], marker=i + 101
        )  # curves are marked 1-based with a 100 offset

    # Create a surface from all curves
    g.surface(list(g.curves.keys()))

    # Create the mesh
    mesh = cfm.GmshMesh(g)
    mesh.el_type = mesh_props.get("el_type")
    mesh.dofs_per_node = mesh_props.get("dofs_per_node")
    mesh.el_size_factor = mesh_props.get("el_size_factor")

    coords, edofs, dofs, bdofs, emarkers = mesh.create()
    return coords, dofs, edofs, bdofs


def load_plane2d_configuration(properties: dict, plane_version: str, mode: str):
    if mode == "predefined":
        plane_data = properties[plane_version]
        points = plane_data["points"]
        elements = plane_data["elements"]
        material_data = plane_data["material_data"]
        boundary_conditions = plane_data["boundary_conditions"]
        forces = plane_data["forces"]
        mesh_props = {
            "el_type": plane_data["el_type"],
            "dofs_per_node": plane_data["dofs_per_node"],
            "el_size_factor": plane_data["el_size_factor"],
        }
        return points, elements, material_data, boundary_conditions, forces, mesh_props

    elif mode == "random":
        plane_data = properties["plane_configurations"][plane_version]
        points = plane_data["points"]
        elements = plane_data["elements"]
        boundary_conditions = plane_data[
            "boundary_conditions"
        ]  # e.g., contains "possible_edges" and "corresponding_points"
        forces = plane_data[
            "forces"
        ]  # e.g., "possible_points", "force_range", "possible_dimensions"
        material_options = properties["materials"]  # Use global materials
        mesh_props = {
            "el_type": plane_data["el_type"],
            "dofs_per_node": plane_data["dofs_per_node"],
            "el_size_factor": plane_data["el_size_factor"],
        }
        return (
            points,
            elements,
            material_options,
            boundary_conditions,
            forces,
            mesh_props,
        )
    else:
        raise ValueError("Unknown mode")


def save_plane2d_input_and_results(simulation_data, data_to_save):
    data_to_save["a"] = list(itertools.chain(*data_to_save["a"]))
    mode, plane2d_version, simulation_index = simulation_data
    os.makedirs(results_dir(), exist_ok=True)

    results_filename = "_".join([mode, plane2d_version, str(simulation_index), "results"]) + ".json"
    results_path = os.path.join(results_dir(), results_filename)

    with open(results_path, "w", encoding="utf-8") as f_out:
        json.dump(data_to_save, f_out, indent=2)


def find_displacement_at_predefined_nodes_in_auto_mesh(
    coords_pre, result_summary, coords_auto, dofs_auto, a_auto
):
    """
    For each node in predefined coords, find the closest node in auto mesh and
    return that node's horizontal & vertical displacement from a_auto.
    """
    results = []
    for i_pre, (x_pre, y_pre) in enumerate(coords_pre):
        # find closest node in coords_auto
        best_index = None
        best_dist_sq = float("inf")
        for i_auto, (x_auto, y_auto) in enumerate(coords_auto):
            dx = x_auto - x_pre
            dy = y_auto - y_pre
            dist_sq = dx * dx + dy * dy
            if dist_sq < best_dist_sq:
                best_dist_sq = dist_sq
                best_index = i_auto

        # once found best_index in auto mesh
        i_node_auto = best_index
        a_index_x = dofs_auto[i_node_auto, 0] - 1
        a_index_y = dofs_auto[i_node_auto, 1] - 1
        ux_auto = a_auto[a_index_x, 0]
        vy_auto = a_auto[a_index_y, 0]

        results.append(
            {
                "i_pre_node": i_pre + 1,
                "pre_node_coords": [float(x_pre), float(y_pre)],
                "auto_node_index": i_node_auto + 1,
                "auto_node_coords": [
                    float(coords_auto[i_node_auto, 0]),
                    float(coords_auto[i_node_auto, 1]),
                ],
                "ux_auto": float(ux_auto),
                "vy_auto": float(vy_auto),
                "distance": float(np.sqrt(best_dist_sq)),
            }
        )
    u_node = result_summary["max_u_node"]
    v_node = result_summary["max_v_node"]
    automesh_corresponding_displacements = {
        "u_val": results[u_node - 1]["ux_auto"],
        "u_node": results[u_node - 1]["auto_node_index"],
        "v_val": results[v_node - 1]["vy_auto"],
        "v_node": results[v_node - 1]["auto_node_index"],
    }

    return automesh_corresponding_displacements


def edofs_to_enodes(edofs, dofs):
    """
    Convert DOF-based 'edofs' (nEls x 6) to node-based 'enodes' (nEls x 3).
    Each row in 'edofs' has 3 nodes, each with 2 DOFs => total 6 columns.
    'dofs' is shape (nNodes, 2), listing the DOF pair [dx, dy] for each node i.

    Parameters
    ----------
    edofs : ndarray of shape (nEls, 6)
        Each row: [dx1, dy1, dx2, dy2, dx3, dy3]
    dofs : ndarray of shape (nNodes, 2)
        dofs[i, :] = [dx_i, dy_i] for node (i+1), 1-based node indexing.

    Returns
    -------
    enodes : ndarray of shape (nEls, 3)
        Each row: [nodeA, nodeB, nodeC] (1-based node indices).
    """

    # 1) Build a lookup dict: (dx, dy) -> node_index (1-based).
    lookup = {}
    for i_node in range(dofs.shape[0]):
        dx_i, dy_i = dofs[i_node]
        lookup[(dx_i, dy_i)] = i_node + 1  # store 1-based

    n_els = edofs.shape[0]
    enodes = np.zeros((n_els, 3), dtype=int)

    # 2) For each element row in edofs,
    #    we have [dx1, dy1, dx2, dy2, dx3, dy3].
    for i_el in range(n_els):
        d = edofs[i_el]
        # d is shape (6,). group them into pairs:
        # node1 has (d[0], d[1]), node2 => (d[2], d[3]), node3 => (d[4], d[5])
        node1 = lookup.get((d[0], d[1]))
        node2 = lookup.get((d[2], d[3]))
        node3 = lookup.get((d[4], d[5]))

        enodes[i_el] = [node1, node2, node3]

    return enodes
