import unittest

import numpy as np

from src.taskgen.core.beam_solver import solve_beam

# from src.solver.beam_plotter import plot_beam_results, plot_beam_displacements


class TestSolver(unittest.TestCase):
    def setUp(self):
        self.geometry = {
            "coord": np.array(
                [
                    [0.0, 0.0],
                    [3.0, 0.0],
                    [3.0, 0.0],
                    [6.0, 0.0],
                    [9.0, 0.0],
                    [12.0, 0.0],
                ]
            ),
            "dof": np.array(
                [
                    [1, 2, 3],
                    [4, 5, 6],
                    [4, 5, 16],
                    [7, 8, 9],
                    [10, 11, 12],
                    [13, 14, 15],
                ]
            ),
            "edof": np.array(
                [
                    [1, 2, 3, 4, 5, 6],
                    [4, 5, 16, 7, 8, 9],
                    [7, 8, 9, 10, 11, 12],
                    [10, 11, 12, 13, 14, 15],
                ]
            ),
            "bc": np.array([1, 2, 3, 8, 14]),
            "ndofs": 16,
            "nels": 4,
        }
        self.element_properties = [
            {
                "material": {"type": "concrete", "E": 30000000.0},
                "section": {"type": "square20", "A": 400, "I": 13333.3},
            },
            {
                "material": {"type": "concrete", "E": 30000000.0},
                "section": {"type": "square20", "A": 400, "I": 13333.3},
            },
            {
                "material": {"type": "concrete", "E": 30000000.0},
                "section": {"type": "square20", "A": 400, "I": 13333.3},
            },
            {
                "material": {"type": "concrete", "E": 30000000.0},
                "section": {"type": "square20", "A": 400, "I": 13333.3},
            },
        ]
        self.loads = {
            "P_loc": 4,  # (DOF number - 1) for concentrated force
            "P": 5,
            "q_loc": [2, 3],  # (Element number -1) for distributed load
            "q": [-2, -2],  # Magnitude of distributed load per unit length
        }

    def test_solve_beam(self):
        a, ex, ey, element_results, max_results = solve_beam(
            self.geometry, self.element_properties, self.loads
        )

        expected_displacements = np.array(
            [
                0.00000000e00,
                0.00000000e00,
                0.00000000e00,
                0.00000000e00,
                1.18125295e-02,
                5.90626477e-03,
                0.00000000e00,
                0.00000000e00,
                -4.12501031e-03,
                0.00000000e00,
                -8.01564504e-03,
                -4.68751172e-05,
                0.00000000e00,
                0.00000000e00,
                4.31251078e-03,
                -3.84375961e-03,
            ]
        )
        computed_displacements = np.array(a).flatten()

        np.testing.assert_allclose(
            computed_displacements,
            expected_displacements,
            rtol=1e-3,
            err_msg="Computed displacements do not match expected values",
        )


if __name__ == "__main__":
    unittest.main()
