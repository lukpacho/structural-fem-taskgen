import os
import json
import numpy as np
import random
from pprint import pprint


def load_properties(path):
    with open(path, 'r') as file:
        return json.load(file)


def generate_geometry(version, properties):
    config = properties["beam_configurations"][str(version)]
    n_elements = config["n_elements"]
    length_options = config["lengths"]
    hinges = config.get("hinges", [])  # Hinges indicated by the first node of the hinge
    lengths = [random.choice(length_options) for _ in range(n_elements)]
    coords = np.append(np.array([0]), np.cumsum(lengths))

    coord_list = []
    dof_list = []
    edof_list = []
    dof_counter = 1

    # Generate coordinates and initial DOFs
    for i in range(n_elements + 1):  # +1 because we have one more node than elements
        coord_list.append([coords[i], 0])
        if i in hinges:
            # This node is the start of a hinge, so repeat it for a shared odd DOF scenario
            coord_list.append([coords[i], 0])
            # Assign DOFs: first node in hinge retains the sequence, second repeats the odd DOF
            dof_list.append([dof_counter, dof_counter + 1])
            dof_counter += 2
            dof_list.append([dof_counter - 2, dof_counter])  # Shared odd DOF
            dof_counter += 1  # Increment only once since odd DOF was shared
        else:
            # Normal node DOF assignment
            dof_list.append([dof_counter, dof_counter + 1])
            dof_counter += 2

    # Convert to NumPy arrays
    coord = np.array(coord_list)
    dof = np.array(dof_list)

    edof_counter = 0

    for i in range(n_elements):
        if i+1 in hinges:
            edof_list.append(dof_list[edof_counter] + dof_list[edof_counter + 1])
            edof_counter += 2
        else:
            edof_list.append(dof_list[edof_counter] + dof_list[edof_counter + 1])
            edof_counter += 1

    edof = np.array(edof_list)

    bc = np.array(config["boundary_conditions"])

    geometry = {
        'coord': coord,
        'dof': dof,
        'edof': edof,
        'bc': bc,
        'ndofs': np.max(dof),
        'nels': n_elements,
        'L': lengths
    }
    return geometry, max(lengths)


def generate_element_properties(geometry, properties):
    """
    Generates random materials and sections for each element based on version-specific configurations.
    """
    n_elements = geometry['nels']
    materials = properties['materials']
    sections = properties['sections']

    element_properties = []
    for _ in range(n_elements):
        selected_material_key = random.choice(list(materials.keys()))
        selected_section_key = random.choice(list(sections.keys()))

        selected_material = materials[selected_material_key]
        selected_section = sections[selected_section_key]

        element_properties.append({
            'material': {
                'type': selected_material_key,
                'E': selected_material['E']
            },
            'section': {
                'type': selected_section_key,
                'A': selected_section['A'],
                'I': selected_section['I']
            }
        })
    return element_properties


def generate_loads(geometry, properties):
    """
    Generates random loads considering available DOF locations and excluding boundary conditions.
    """
    dof = geometry['dof']
    bc = geometry['bc']
    n_elements = geometry['nels']
    loads = properties['loads']

    # Filter DOF locations that are not restricted by boundary conditions
    valid_p_locs = [dof[i, 0] for i in range(len(dof)) if dof[i, 0] not in bc]
    valid_m_locs = [dof[i, 1] for i in range(len(dof)) if dof[i, 1] not in bc]

    P = random.choice(loads['P'])
    M = random.choice(loads['M'])
    q = random.choice(loads['q'])

    P_loc = random.choice(valid_p_locs)-1 if valid_p_locs else None
    M_loc = random.choice(valid_m_locs)-1 if valid_m_locs else None
    q_loc = random.randint(0, n_elements-1)  # Continuous loads may apply to any element

    return {
        'P': P,
        'P_loc': P_loc,
        'M': M,
        'M_loc': M_loc,
        'q': q,
        'q_loc': q_loc
    }


if __name__ == '__main__':
    current_dir = os.path.dirname(os.path.abspath(__file__))
    properties_path = os.path.join(current_dir, '..', 'data', 'properties.json')
    properties = load_properties(properties_path)
    version = 3
    geometry, max_length = generate_geometry(version, properties)
    pprint(["Selected Geometry:", geometry])
    element_properties = generate_element_properties(geometry, properties)
    pprint(["Selected Materials and Sections:", element_properties])
    loads = generate_loads(geometry, properties)
    pprint(["Generated Loads:", loads])
