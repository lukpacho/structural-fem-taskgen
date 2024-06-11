import unittest
import json
import os
import numpy as np
from unittest.mock import patch
from src.solver.beam_solver import solve_beam


class TestSolver(unittest.TestCase):
    def setUp(self):
        self.geometry = {
            'coord': np.array([[0., 0.],
                               [3., 0.],
                               [3., 0.],
                               [6., 0.],
                               [9., 0.],
                               [12., 0.]]),
            'dof': np.array([[1, 2],
                             [3, 4],
                             [3, 5],
                             [6, 7],
                             [8, 9],
                             [10, 11]]),
            'edof': np.array([[1, 2, 3, 4],
                              [3, 5, 6, 7],
                              [6, 7, 8, 9],
                              [8, 9, 10, 11]]),
            'bc': np.array([1, 2, 6, 10]),
            'ndofs': 11,
            'nels': 4
        }
        self.element_properties = [
            {'material': {'type': 'concrete', 'E': 30000000.0},
             'section': {'type': 'square20', 'A': 400, 'I': 13333.3}},
            {'material': {'type': 'concrete', 'E': 30000000.0},
             'section': {'type': 'square20', 'A': 400, 'I': 13333.3}},
            {'material': {'type': 'concrete', 'E': 30000000.0},
             'section': {'type': 'square20', 'A': 400, 'I': 13333.3}},
            {'material': {'type': 'concrete', 'E': 30000000.0},
             'section': {'type': 'square20', 'A': 400, 'I': 13333.3}}
        ]
        self.loads = {
            'P_loc': 2,
            'P': 5,
            'q_loc': [2, 3],  # Element number for distributed load
            'q': -2  # Magnitude of distributed load per unit length
        }

    def test_solve_beam(self):
        a, ex, ey, ed, element_results = solve_beam(self.geometry, self.element_properties, self.loads)

        expected_displacements = np.array([0.0000e+00, 0.0000e+00, 1.1813e-02, 5.9063e-03,
                                           -3.8438e-03, 0.0000e+00, -4.1250e-03, -8.0156e-03,
                                           -4.6875e-05, 0.0000e+00, 4.3125e-03])
        computed_displacements = np.array(a).flatten()

        np.testing.assert_allclose(
            computed_displacements, expected_displacements, rtol=1e-3,
            err_msg="Computed displacements do not match expected values"
        )


if __name__ == '__main__':
    unittest.main()
