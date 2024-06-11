import unittest
import json
import os
import numpy as np
from unittest.mock import patch
from src.generator import generate_geometry, generate_element_properties, generate_loads


class TestGenerator(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Load the properties JSON file once and use it for all tests
        current_dir = os.path.dirname(os.path.abspath(__file__))
        properties_path = os.path.join(current_dir, '..', 'data', 'properties.json')
        with open(properties_path, 'r') as file:
            cls.properties = json.load(file)

    def check_hinges(self, version, geometry):
        # Verify that for each hinge in the properties, the corresponding
        # nodes in the geometry actually share the specified DOFs
        hinges_info = self.properties['beam_configurations'][str(version)]['hinges']
        for hinge_index in hinges_info:
            node1, node2 = hinge_index, hinge_index + 1
            if geometry['dof'][node1][0] != geometry['dof'][node2][0]:
                return False
        return True

    def test_generate_geometry_detailed_checks(self):
        for version in self.properties['beam_configurations'].keys():
            with self.subTest(version=version):
                geometry, max_length = generate_geometry(version, self.properties)
                self.assertIsInstance(geometry, dict)
                self.assertGreater(max_length, 0)
                self.assertIn('coord', geometry)
                if 'hinges' in self.properties['beam_configurations'][version]:
                    self.assertTrue(self.check_hinges(version, geometry))

    def test_edof_generation_version_2(self):
        version = '2'  # assuming versions are stored as strings in JSON
        geometry, _ = generate_geometry(version, self.properties)
        expected_edof = [
            [1, 1, 2, 3, 4],
            [2, 3, 5, 6, 7],
            [3, 6, 7, 8, 9],
            [4, 8, 9, 10, 11],
            [5, 10, 11, 12, 13],
            [6, 12, 13, 14, 15],
        ]
        self.assertEqual(geometry['edof'].tolist(), expected_edof)

    def test_edof_generation_version_3(self):
        version = '3'  # another version for testing
        geometry, _ = generate_geometry(version, self.properties)
        # Define expected edof based on version 3 configurations
        expected_edof = [
            [1, 1, 2, 3, 4],
            [2, 3, 4, 5, 6],
            [3, 5, 7, 8, 9],
            [4, 8, 9, 10, 11],
            [5, 10, 11, 12, 13],
            [6, 12, 13, 14, 15],
        ]
        self.assertEqual(geometry['edof'].tolist(), expected_edof)

    def test_edof_generation_version_8(self):
        version = '8'  # another version for testing
        geometry, _ = generate_geometry(version, self.properties)
        # Define expected edof based on version 3 configurations
        expected_edof = [
            [1, 1, 2, 3, 4],
            [2, 3, 4, 5, 6],
            [3, 5, 6, 7, 8],
            [4, 7, 9, 10, 11],
            [5, 10, 11, 12, 13],
            [6, 12, 13, 14, 15],
        ]
        self.assertEqual(geometry['edof'].tolist(), expected_edof)

    @patch('random.choice')
    def test_generate_element_properties(self, mocked_choice):
        mocked_choice.side_effect = lambda x: x[0]
        geometry = {'nels': 6}
        element_properties = generate_element_properties(geometry, self.properties)
        first_material_key = list(self.properties['materials'].keys())[0]
        first_section_key = list(self.properties['sections'].keys())[0]
        self.assertEqual(element_properties[0]['material']['type'], first_material_key)
        self.assertEqual(element_properties[0]['section']['type'], first_section_key)

    @patch('random.choice')
    def test_generate_loads(self, mocked_choice):
        mocked_choice.side_effect = lambda x: x[0]
        geometry = {
            'dof': np.array([[1, 2], [3, 4]]),
            'bc': np.array([[1, 0], [2, 0]]),
            'nels': 2
        }
        loads = generate_loads(geometry, self.properties)
        first_P = self.properties['loads']['P'][0]
        first_M = self.properties['loads']['M'][0]
        self.assertEqual(loads['P'], first_P)
        self.assertEqual(loads['M'], first_M)


if __name__ == '__main__':
    unittest.main()
