import unittest
import os
import numpy as np
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings("ignore", category=PendingDeprecationWarning)

# CalFEM for Python
import calfem.core as cfc
import calfem.geometry as cfg
import calfem.mesh as cfm
import calfem.vis_mpl as cfv

from config import BASE_DIR, cm_to_in
from src.solver.plane2d_solver import solve_plane2d, build_plane2d_with_predefined_mesh, build_plane2d_with_auto_mesh
from src.solver.plane2d_plotter import plot_predefined_mesh, plot_auto_mesh


class TestPlane2DSolver(unittest.TestCase):
    def test_cantilever_example(self):
        # -----------------------------
        # 1) SETUP PROBLEM DEFINITIONS
        # -----------------------------
        mesh_props = {
            "el_type": 2,  # 2 = Triangles, 3 = Quads
            "dofs_per_node": 2,
            "el_size_factor": 0.1
        }

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
                "marker": 108,
                "value": 0.0,
                "dimension": 0
            }
        }

        loads = {
            "force1": {
                "type": "point",
                "point": 4,  # 1-based ID
                "marker": 4,
                "value": 100.0,
                "dimension": 1
            },
            "force2": {
                "type": "point",
                "point": 5,  # 1-based ID
                "marker": 5,
                "value": -100.0,
                "dimension": 1
            }
        }
        simulation_data = ["test", "test", "test"]

        # -----------------------------------------
        # 2.1) BUILD PREDEFINED MESH & PLOT
        # -----------------------------------------
        coords, dofs, edofs, bdofs = build_plane2d_with_predefined_mesh(
            points, elements, boundary_conditions, loads
        )
        plot_predefined_mesh(coords, dofs, edofs, mesh_props, simulation_data)

        # -----------------------------------------
        # 2.2) SOLVE THE PREDEFINED MESH
        # -----------------------------------------
        a, r, es, ed, results_summary = solve_plane2d(
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
        # 3.1) BUILD GMSH-BASED MESH (AUTO) & PLOT
        # -----------------------------------------
        coords_auto, dofs_auto, edofs_auto, bdofs_auto = build_plane2d_with_auto_mesh(
            points, boundary_conditions, loads, mesh_props
        )
        plot_auto_mesh(coords_auto, edofs_auto, mesh_props, simulation_data)

        # -----------------------------------------
        # 3.2) SOLVE THE AUTO-GENERATED MESH
        # -----------------------------------------
        a_auto, r_auto, es_auto, ed_auto, results_summary_auto = solve_plane2d(
            coords_auto, dofs_auto, edofs_auto, bdofs_auto,
            material_data, boundary_conditions, loads
        )
        self.assertEqual(a_auto.shape[0], coords_auto.shape[0] * 2,
                         "Auto mesh: displacement vector length mismatch.")
        self.assertFalse(np.allclose(a_auto, 0), "All zero displacements suspicious for auto mesh.")



if __name__ == '__main__':
    unittest.main()
