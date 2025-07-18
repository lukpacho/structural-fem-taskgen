import unittest
from unittest.mock import patch

import numpy as np

from src.taskgen.core.beam_generator import (
    generate_element_properties,
    generate_geometry,
    generate_loads,
)
from src.taskgen.core.config import load_properties


class TestGenerator(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Load the properties JSON file once and use it for all tests
        cls.properties = load_properties()["random"]

    def test_generate_geometry_detailed_checks(self):
        for version in self.properties["beam_configurations"].keys():
            with self.subTest(version=version):
                geometry, max_length = generate_geometry(version, self.properties)
                self.assertIsInstance(geometry, dict)
                self.assertGreater(max_length, 0)
                self.assertIn("coord", geometry)

    def test_edof_generation_version_2(self):
        version = "beam2"
        geometry, _ = generate_geometry(version, self.properties)
        expected_edof = [
            [1, 2, 3, 4, 5, 6],
            [4, 5, 22, 7, 8, 9],
            [7, 8, 9, 10, 11, 12],
            [10, 11, 12, 13, 14, 15],
            [13, 14, 15, 16, 17, 18],
            [16, 17, 18, 19, 20, 21],
        ]
        self.assertEqual(geometry["edof"].tolist(), expected_edof)

    def test_edof_generation_version_3(self):
        version = "beam3"
        geometry, _ = generate_geometry(version, self.properties)
        expected_edof = [
            [1, 2, 3, 4, 5, 6],
            [4, 5, 6, 7, 8, 9],
            [7, 8, 22, 10, 11, 12],
            [10, 11, 12, 13, 14, 15],
            [13, 14, 15, 16, 17, 18],
            [16, 17, 18, 19, 20, 21],
        ]
        self.assertEqual(geometry["edof"].tolist(), expected_edof)

    def test_edof_generation_version_8(self):
        version = "beam8"
        geometry, _ = generate_geometry(version, self.properties)
        expected_edof = [
            [1, 2, 3, 4, 5, 6],
            [4, 5, 6, 7, 8, 9],
            [7, 8, 9, 10, 11, 12],
            [10, 11, 22, 13, 14, 15],
            [13, 14, 15, 16, 17, 18],
            [16, 17, 18, 19, 20, 21],
        ]
        self.assertEqual(geometry["edof"].tolist(), expected_edof)

    @patch("random.choice")
    def test_generate_element_properties(self, mocked_choice):
        mocked_choice.side_effect = lambda x: x[0]
        geometry = {"nels": 6}
        element_properties = generate_element_properties(geometry, self.properties)
        first_material_key = list(self.properties["materials"].keys())[0]
        first_section_key = list(self.properties["sections"].keys())[0]
        self.assertEqual(element_properties[0]["material"]["type"], first_material_key)
        self.assertEqual(element_properties[0]["section"]["type"], first_section_key)

    @patch("random.choice")
    def test_generate_loads(self, mocked_choice):
        mocked_choice.side_effect = lambda x: x[0]
        geometry = {
            "dof": np.array([[1, 2, 3], [4, 5, 6]]),
            "bc": np.array([1, 2, 5]),
            "nels": 1,
        }
        loads = generate_loads(geometry, self.properties)
        first_q = self.properties["forces"]["q"][0]
        first_M = self.properties["forces"]["M"][0]
        self.assertEqual(loads["q"][0], first_q)
        self.assertEqual(loads["M"][0], first_M)


if __name__ == "__main__":
    unittest.main()
