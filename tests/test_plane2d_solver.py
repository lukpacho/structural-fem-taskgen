import unittest
import os
import numpy as np
from config import BASE_DIR, cm_to_in
from matplotlib.backends.backend_pdf import PdfPages

import calfem.core as cfc
import calfem.geometry as cfg
import calfem.mesh as cfm
import calfem.vis_mpl as cfv
import matplotlib.pyplot as plt

from src.solver.plane2d_solver import solve_plane2d


class TestPlane2DSolver(unittest.TestCase):
    def test_cantilever_example(self):
        el_type = 2  # 2 - Triangles, 3 - Quads
        dofs_per_node = 2

        material_data = {
            "ptype": 1,  # plane stress (or 2 for plane strain)
            "E": 50e6,
            "nu": 0.3,
            "t": 0.1
        }

        # Definition of boundary conditions and loads
        # dimension: 0 => all directions, 1 => x-direction, 2 => y-direction
        boundary_conditions = {
            "bc1": {
                "type": "line",
                "marker": 10,
                "value": 0.0,
                "dimension": 0
            }
        }

        loads = {
            "force1": {
                "marker": 1,
                "value": 100.0,
                "dimension": 1
            },
            "force2": {
                "marker": 2,
                "value": -100.0,
                "dimension": 1
            }
        }

        # Hardcode a known geometry, bc, loads from your snippet
        g = cfg.geometry()

        g.point([0.0, 0.0])  # ID=0
        g.point([1.0, 0.0])  # ID=1
        g.point([2.0, 0.0])  # ID=2
        g.point([3.0, 0.0])  # ID=3
        g.point([3.0, 1.0])  # ID=4
        g.point([2.0, 1.0])  # ID=5
        g.point([1.0, 1.0])  # ID=6
        g.point([0.0, 1.0])  # ID=7

        g.setPointMarker(ID=3, marker=loads["force1"]["marker"])
        g.setPointMarker(ID=4, marker=loads["force2"]["marker"])

        g.spline([0, 1])
        g.spline([1, 2])
        g.spline([2, 3])
        g.spline([3, 4])
        g.spline([4, 5])
        g.spline([5, 6])
        g.spline([6, 7])
        g.spline([7, 0], marker=boundary_conditions["bc1"]["marker"])

        elements_on_curve = 1
        for curve in g.curves.values():
            curve[3] = elements_on_curve

        g.surface([0, 1, 2, 3, 4, 5, 6, 7])

        mesh = cfm.GmshMesh(g)
        mesh.el_type = el_type
        mesh.dofs_per_node = dofs_per_node
        mesh.el_size_factor = 1.0
        mesh.min_size = 1
        mesh.meshing_algorithm = '1'  # auto => default

        coords, edofs, dofs, bdofs, element_markers = mesh.create()

        # Plot & save to data/temp for debugging
        ex, ey = cfc.coordxtr(edofs, coords, dofs)
        fig, ax = plt.subplots(figsize=(16 * cm_to_in, 8 * cm_to_in))
        cfv.draw_mesh(coords, edofs, mesh.dofs_per_node, mesh.el_type, filled=True)
        cfv.draw_node_circles(ex, ey)
        temp_fig_path = os.path.join(BASE_DIR, "data", "temp", "cantilever_mesh.pdf")
        fig.savefig(temp_fig_path, format='pdf')
        plt.close(fig)

        a, r, es, ed = solve_plane2d(coords, dofs, edofs, bdofs, material_data, boundary_conditions, loads)


        self.assertEqual(a.shape[0], coords.shape[0] * 2)  # dofs = nodes*2
        self.assertFalse(np.allclose(a, 0), "All zero displacements suspicious.")

if __name__ == '__main__':
    unittest.main()
