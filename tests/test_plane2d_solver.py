import unittest
import os
import itertools
import numpy as np
import matplotlib.pyplot as plt

# CalFEM for Python
import calfem.core as cfc
import calfem.geometry as cfg
import calfem.mesh as cfm
import calfem.vis_mpl as cfv

from config import BASE_DIR, cm_to_in
from src.solver.plane2d_solver import solve_plane2d


def draw_node_numbers(ax, coords, color='blue'):
    """
    Draw node numbering at each (x,y) in coords with a white-translucent box.
    """
    offset_x = 0.1
    offset_y = 0.1
    for i, (x, y) in enumerate(coords):
        ax.text(
            x + offset_x, y + offset_y, str(i + 1),
            color=color,
            ha='center', va='center',
            bbox=dict(facecolor='white', alpha=0.7, edgecolor='none'),
            zorder=5
        )


def draw_element_numbers(ax, ex, ey, color='red'):
    """
    Draw element numbering near each element's centroid with a white-translucent box.

    ex, ey shape: (n_elements, n_nodes_per_element)
    We'll label each element i with its index i+1 at the centroid.
    """
    for i in range(ex.shape[0]):
        cx = np.mean(ex[i])
        cy = np.mean(ey[i])
        ax.text(
            cx, cy, str(i + 1),
            color=color,
            ha='center', va='center',
            bbox=dict(facecolor='white', alpha=0.7, edgecolor='none'),
            zorder=5
        )


class TestPlane2DSolver(unittest.TestCase):
    def test_cantilever_example(self):
        """
        1) Use a predefined mesh (coords, elements).
        2) Solve the plane problem.
        3) Plot with node & element numbering in different colors.
        4) Then build a geometry for Gmsh, solve again with a smaller el_size_factor, plot, etc.
        """

        # -----------------------------
        # 1) SETUP PROBLEM DEFINITIONS
        # -----------------------------
        el_type = 2  # 2 = Triangles, 3 = Quads
        dofs_per_node = 2
        el_size_factor = 0.1

        material_data = {
            "ptype": 1,  # plane stress (or 2 for plane strain)
            "E": 50e6,
            "nu": 0.3,
            "t": 0.1
        }

        # Predefined mesh data
        points = [
            [0.0, 0.0],
            [1.0, 0.0],
            [2.0, 0.0],
            [3.0, 0.0],
            [3.0, 1.0],
            [2.0, 1.0],
            [1.0, 1.0],
            [0.0, 1.0]
        ]

        # Each element is 3 node indices => triangular
        # (Indices here are 1-based, we’ll convert to 0-based for array access)
        elements = [
            [1, 7, 8],
            [1, 2, 7],
            [2, 6, 7],
            [2, 3, 6],
            [3, 5, 6],
            [3, 4, 5]
        ]

        # Definition of boundary conditions and loads
        # dimension: 0 => fix x & y-directions
        # dimension: 1 => fix x-direction
        # dimension: 2 => fix y-direction
        boundary_conditions = {
            "bc1": {
                "type": "line",
                "edge": 8,
                "points": [8, 1],  # 1-based node indices
                "marker": 10,
                "value": 0.0,
                "dimension": 0
            }
        }

        loads = {
            "force1": {
                "type": "point",
                "point": 4,  # 1-based ID
                "marker": 1,
                "value": 100.0,
                "dimension": 1
            },
            "force2": {
                "type": "point",
                "point": 5,  # 1-based ID
                "marker": 2,
                "value": -100.0,
                "dimension": 1
            }
        }

        # --------------------------------------------
        # 2) BUILD PREDEFINED MESH COORD & EDOF ARRAYS
        # --------------------------------------------
        coords= np.array(points)
        n_nodes = len(coords)

        # We'll define dofs for each node as (2i+1, 2i+2) => 1-based DOF indices
        dofs = np.array([[2 * node + 1, 2 * node + 2] for node in range(n_nodes)], dtype=int)

        # Build edofs array from the elements
        edofs_list = []
        for elem in elements:
            n1, n2, n3 = (elem[0] - 1, elem[1] - 1, elem[2] - 1)
            edofs_list.append([*dofs[n1], *dofs[n2], *dofs[n3]])
        edofs = np.array(edofs_list, dtype='int32')

        # Build bdofs from boundary_conditions & loads
        bdofs = {}
        # 2a) Boundary conditions
        for _, bc_data in boundary_conditions.items():
            marker = bc_data["marker"]
            dofs_of_points = []
            for pt in bc_data["points"]:
                point_id = pt - 1  # bc_data["points"] node IDs => 1-based
                dofs_of_points.append(dofs[point_id].tolist())
            bdofs[int(marker)] = list(itertools.chain(*dofs_of_points))

        # 2b) Loads
        for _, force_data in loads.items():
            marker = force_data["marker"]
            point_id = force_data["point"] - 1  # 0-based
            bdofs[int(marker)] = dofs[point_id].tolist()

        # -----------------------------------------
        # 3) PLOT PREDEFINED MESH WITH NUMBERING
        # -----------------------------------------
        ex, ey = cfc.coordxtr(edofs, coords, dofs)

        fig, ax = plt.subplots(figsize=(16 * cm_to_in, 8 * cm_to_in))
        cfv.draw_mesh(coords, edofs, dofs_per_node, el_type, filled=True)
        cfv.draw_node_circles(ex, ey, filled=True, marker_type='.')
        draw_node_numbers(ax, coords, color='blue')
        draw_element_numbers(ax, ex, ey, color='red')

        # Save figure
        temp_fig_path = os.path.join(BASE_DIR, "data", "temp", "cantilever_mesh_predefined.pdf")
        fig.savefig(temp_fig_path, format='pdf')
        plt.close(fig)

        # -----------------------------------------
        # 4) SOLVE THE PREDEFINED MESH
        # -----------------------------------------
        a, r, es, ed = solve_plane2d(
            coords, dofs, edofs, bdofs,
            material_data, boundary_conditions, loads
        )

        # Basic checks
        self.assertEqual(a.shape[0], coords.shape[0] * 2, "Displacement vector length mismatch.")
        self.assertFalse(np.allclose(a, 0), "All zero displacements suspicious for predefined mesh.")

        # Compare a few known DOFs vs reference
        values_to_test = np.squeeze(np.asarray(a[[6, 7]]))  # flatten DOFs 6,7
        reference_values = np.array([8.81208055814559e-05, 0.000256323384661279], dtype='float64')
        for i in range(len(values_to_test)):
            self.assertAlmostEqual(values_to_test[i], reference_values[i], places=9)

        # -----------------------------------------
        # 5) BUILD GMSH-BASED MESH (AUTO) & PLOT
        # -----------------------------------------
        g = cfg.geometry()

        for (x, y) in coords:
            g.point([x, y])

        # Assign point markers for loads
        for _, force_data in loads.items():
            marker = force_data["marker"]
            point_id = force_data["point"] - 1  # 0-based
            g.setPointMarker(ID=point_id, marker=marker)

        n_points_geom = len(g.points)

        # Build splines in a loop => closed loop
        for i in range(n_points_geom):
            start_node = i
            end_node = (i + 1) % n_points_geom
            g.spline([start_node, end_node])

        # Mark a specific curve if desired:
        for _, bc_data in boundary_conditions.items():
            edge_id = bc_data["edge"] - 1  # user gave "edge":8 => 1-based
            marker = bc_data["marker"]
            g.setCurveMarker(ID=edge_id, marker=marker)

        # Create a surface from all curves
        g.surface(list(g.curves.keys()))

        # Create the mesh
        mesh = cfm.GmshMesh(g)
        mesh.el_type = el_type
        mesh.dofs_per_node = dofs_per_node
        mesh.el_size_factor = el_size_factor

        coords_auto, edofs_auto, dofs_auto, bdofs_auto, emarkers_auto = mesh.create()

        # Plot the automatically generated mesh
        fig, ax = plt.subplots(figsize=(16 * cm_to_in, 8 * cm_to_in))
        cfv.draw_mesh(coords_auto, edofs_auto, dofs_per_node, el_type=el_type, filled=True)
        temp_fig_path = os.path.join(BASE_DIR, "data", "temp", "cantilever_mesh_auto.pdf")
        fig.savefig(temp_fig_path, format='pdf')
        plt.close(fig)

        # -----------------------------------------
        # 6) SOLVE THE AUTO-GENERATED MESH
        # -----------------------------------------
        a_auto, r_auto, es_auto, ed_auto = solve_plane2d(
            coords_auto, dofs_auto, edofs_auto, bdofs_auto,
            material_data, boundary_conditions, loads
        )
        self.assertEqual(a_auto.shape[0], coords_auto.shape[0] * 2,
                         "Auto mesh: displacement vector length mismatch.")
        self.assertFalse(np.allclose(a_auto, 0), "All zero displacements suspicious for auto mesh.")



if __name__ == '__main__':
    unittest.main()
