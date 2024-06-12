import os
import json
import numpy as np
import random
from pprint import pprint
from config import BASE_DIR


def load_properties(path):
    with open(path, 'r') as file:
        return json.load(file)


def save_beam_input(geometry, element_properties, loads, mode, beam_version, simulation_index=0):
    """
    Save the beam input data (geometry, element properties, and loads) to a JSON file.

    Parameters:
    - geometry: Dictionary containing geometry details of the beam.
    - element_properties: List of dictionaries, each containing properties of an element.
    - loads: Dictionary containing the loads applied to the beam.
    - mode: Operation mode (e.g., 'random', 'predefined').
    - beam_version: Version identifier for the beam.
    - simulation_index: Optional index for distinguishing between multiple generated simulations.
    """
    input_filename = f'{mode}_{beam_version}_{simulation_index}_input.json'
    path = os.path.join(BASE_DIR, 'data', 'results', input_filename)

    data = {
        "geometry": convert_to_json_serializable(geometry),
        "element_properties": convert_to_json_serializable(element_properties),
        "loads": convert_to_json_serializable(loads)
    }

    with open(path, 'w') as file:
        json.dump(data, file, indent=2)


def convert_to_json_serializable(data):
    """
    Recursively convert numpy data types in a data structure to native Python types
    compatible with JSON serialization.

    Args:
    data: A complex data structure possibly containing numpy types.

    Returns:
    The data structure with all numpy types converted to native Python types.
    """
    if isinstance(data, np.ndarray):
        return data.tolist()
    elif isinstance(data, (np.int_, np.intc, np.intp, np.int8,
                           np.int16, np.int32, np.int64, np.uint8,
                           np.uint16, np.uint32, np.uint64)):
        return int(data)
    elif isinstance(data, (np.float_, np.float16, np.float32, np.float64)):
        return float(data)
    elif isinstance(data, np.bool_):
        return bool(data)
    elif isinstance(data, dict):
        return {k: convert_to_json_serializable(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [convert_to_json_serializable(item) for item in data]
    elif isinstance(data, tuple):
        return tuple(convert_to_json_serializable(item) for item in data)
    else:
        return data


def generate_geometry(version, properties):
    config = properties["beam_configurations"][version]
    n_elements = config["n_elements"]
    length_options = config["lengths"]
    hinges = config.get("hinges", [])  # Hinges indicated by the first node of the hinge
    lengths = [random.choice(length_options) for _ in range(n_elements)]
    coords = np.append(np.array([0]), np.cumsum(lengths))

    dofs_per_node = 3
    n_nodes = n_elements + 1
    coord_list = []
    dof_list = []
    edof_list = []
    hinge_counter = n_nodes * dofs_per_node + 1  # Hinge numbering starts after all regular DOFs

    # Generate coordinates and initial DOFs
    for node in range(n_nodes):
        coord_list.append([coords[node], 0])
        current_dof = dofs_per_node * node + 1
        dof_list.append([current_dof, current_dof + 1, current_dof + 2])
        if node in hinges:
            # This node is the start of a hinge, so repeat it for a shared DOFs scenario
            coord_list.append([coords[node], 0])
            dof_list.append([current_dof, current_dof + 1, hinge_counter])
            hinge_counter += 1

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
    valid_p_locs = [dof[i, 1] for i in range(len(dof)) if dof[i, 1] not in bc]
    valid_m_locs = [dof[i, 2] for i in range(len(dof)) if dof[i, 2] not in bc]

    # Remove duplicates from a list
    valid_p_locs = list(dict.fromkeys(valid_p_locs))

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
    version = 'beam3'
    properties_path = os.path.join(BASE_DIR, 'data', 'properties.json')
    properties = load_properties(properties_path)['random']
    geometry, max_length = generate_geometry(version, properties)
    pprint(["Selected Geometry:", geometry])
    element_properties = generate_element_properties(geometry, properties)
    pprint(["Selected Materials and Sections:", element_properties])
    loads = generate_loads(geometry, properties)
    pprint(["Generated Loads:", loads])
