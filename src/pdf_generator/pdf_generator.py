import subprocess
import os
import shutil
import re
from config import LATEX_TEMPLATES_DIR, PDFS_DIR, TEMP_DIR
from datetime import datetime


def latex_jinja_env(template_folder=LATEX_TEMPLATES_DIR):
    """
    Create a Jinja2 environment that can parse LaTeX templates.
    """
    from jinja2 import Environment, FileSystemLoader
    return Environment(
        block_start_string='\BLOCK{',
        block_end_string='}',
        variable_start_string='\VAR{',
        variable_end_string='}',
        comment_start_string='\#{',
        comment_end_string='}',
        line_statement_prefix='%%',
        line_comment_prefix='%#',
        trim_blocks=True,
        lstrip_blocks=True,
        autoescape=False,
        loader=FileSystemLoader(searchpath=template_folder)
    )


def render_latex_template(template_file, output_name, data):
    template_env = latex_jinja_env()
    template = template_env.get_template(template_file)

    output_text = template.render(data)
    with open(os.path.join(TEMP_DIR, f'{output_name}.tex'), "w", encoding='utf-8') as text_file:
        text_file.write(output_text)


def compile_latex_to_pdf(output_name):
    """
    Compiles the LaTeX file to PDF using lualatex and manages the output.
    :param output_name: The base name of the tex file without extension.
    """
    subprocess.run([
        "lualatex",
        "--shell-escape",
        "--enable-write18",
        f"--output-directory={TEMP_DIR}",
        f"{output_name}.tex"
    ], check=True)

    pdf_file = f"{output_name}.pdf"
    tex_file = f"{output_name}.tex"

    shutil.move(os.path.join(TEMP_DIR, pdf_file), os.path.join(PDFS_DIR, pdf_file))
    shutil.move(os.path.join(TEMP_DIR, tex_file), os.path.join(PDFS_DIR, tex_file))

    for file in os.listdir(TEMP_DIR):
        os.remove(os.path.join(TEMP_DIR, file))


def generate_beam_pdf(template_file, output_name, data):
    """
    Generate a PDF report from a LaTeX template and provided data.
    :param template_file: Path to the Jinja2 templated LaTeX file.
    :param data: Dictionary containing the data to render into the template.
    :param output_name: Base name for the output tex and PDF files.
    """
    current_year = datetime.now().year
    academic_year = f"{current_year}/{current_year + 1}"
    data.update({
        'academic_year': academic_year
    })
    render_latex_template(template_file, output_name, data)
    compile_latex_to_pdf(output_name)


def prepare_nodes_hinges_and_dof_mapping(geometry):
    coord_to_node = {}
    nodes = []
    hinges = []
    dof_to_node = {}
    dof_types = ['x', 'y', 'rotation']

    for idx, coord in enumerate(geometry['coord']):
        coord_tuple = tuple(coord)
        if coord_tuple in coord_to_node:
            node_name = coord_to_node[coord_tuple]
            if node_name not in hinges:
                hinges.append(node_name)
        else:
            node_name = f'n{len(nodes) + 1}'
            nodes.append({'name': node_name, 'x': coord[0], 'y': coord[1]})
            coord_to_node[coord_tuple] = node_name

        dofs = geometry['dof'][idx]
        for i, dof in enumerate(dofs):
            dof_type = dof_types[i % 3]
            dof_to_node[dof] = {'node': node_name, 'type': dof_type}

    return nodes, hinges, dof_to_node


def prepare_elements(geometry, dof_to_node):
    elements = []
    for idx, edof in enumerate(geometry['edof']):
        start_dof = edof[:3]
        end_dof = edof[3:6]

        start_node = dof_to_node[start_dof[0]]['node']
        end_node = dof_to_node[end_dof[0]]['node']

        if start_node != end_node:
            elements.append({'start': start_node, 'end': end_node})
        else:
            print(f"Warning: Element {idx} has the same start node and end node {start_node}.")
    return elements


def determine_supports(geometry, nodes, dof_to_node):
    support_types = {
        1: ('floating bearing', 2),
        2: ('fixed bearing', 1),
        3: ('fixed support', 3)
    }
    node_supports = {}

    # Initialize support records for each boundary condition
    for bc in geometry['bc']:
        if bc in dof_to_node:
            node_name = dof_to_node[bc]['node']
            dof_type = dof_to_node[bc]['type']
            if node_name not in node_supports:
                node_supports[node_name] = set()
            node_supports[node_name].add(dof_type)
        else:
            print(f"Warning: Degree of freedom {bc} was not found in dof_to_node mapping.")

    # Determine the type of support based on the number of dofs constrained
    supports = []
    last_node_name = nodes[-1]['name']
    for node, dof_types in node_supports.items():
        num_constraints = len(dof_types)
        if num_constraints in support_types:
            support_type, type_number = support_types[num_constraints]
            if support_type == 'fixed support':
                rotation = -90 if node == 'n1' else (90 if node == last_node_name else 0)
            else:
                rotation = 0
            supports.append({'node': node, 'type': support_type, 'type_number': type_number, 'rotation': rotation})
        else:
            print(f"Warning: Unsupported number of constraints ({len(dof_types)}) at node {node}.")

    return supports


def prepare_forces(loads, nodes, dof_to_node):
    forces = []
    if 'P' in loads:
        dof_number = loads['P_loc'] + 1
        if dof_number in dof_to_node:
            node_info = dof_to_node[dof_number]
            node_name = node_info['node']
            rotation = -90 if loads['P'] > 0 else 90
            distance = -1.6 if loads['P'] > 0 else 0.1
            forces.append({
                'node': node_name,
                'type': 'point',
                'magnitude': abs(loads['P']),
                'rotation': rotation,
                'length': 1.5,
                'distance': distance
            })
        else:
            print(f"Warning: Degree of freedom {dof_number} was not found in dof_to_node mapping.")
    return forces


def prepare_moments(loads, nodes, hinges, dof_to_node):
    moments = []
    if 'M' in loads:
        dof_number = loads['M_loc'] + 1
        if dof_number in dof_to_node:
            node_info = dof_to_node[dof_number]
            node_name = node_info['node']
            dof_type = node_info['type']
            orientation = 3 if loads['M'] > 0 else 2  # 2 for CW and 3 for CCW rotation
            if node_name in hinges:
                side = 'left' if (dof_number) % 3 < 1 else 'right'
                if side == 'left':
                    rotation = 90
                    label_x_offset = -0.55
                else:
                    rotation = -90
                    label_x_offset = 0.55
                moments.append({
                    'node': node_name,
                    'orientation': orientation,
                    'magnitude': abs(loads['M']),
                    'rotation': rotation,
                    'angle': 200,
                    'distance': 0.5,
                    'label_x_offset': label_x_offset,
                    'label_y_offset': 0.55
                })
            else:
                moments.append({
                    'node': node_name,
                    'orientation': orientation,
                    'magnitude': abs(loads['M']),
                    'rotation': 10,
                    'angle': 200,
                    'distance': 0.5,
                    'label_x_offset': 0.55,
                    'label_y_offset': 0.55
                })
        else:
            print(f"Ostrzeżenie: Stopień swobody {dof_number} nie znaleziony w mapowaniu dof_to_node.")
    return moments


def prepare_lineloads(loads, elements):
    lineloads = []
    if not isinstance(loads['q'], list):
        loads['q'] = [loads['q']]
        loads['q_loc'] = [loads['q_loc']]

    for q_val, q_range in zip(loads['q'], loads['q_loc']):
        start_node = elements[q_range]['start']
        end_node = elements[q_range]['end']
        value = -0.5 if q_val > 0 else 0.5
        distance = 0.4 if q_val > 0 else -0.1
        label_y_offset = 1
        lineloads.append({
            'node1': start_node,
            'node2': end_node,
            'type': 'distributed',
            'value': value,
            'distance': distance,
            'magnitude': abs(q_val),
            'label_y_offset': label_y_offset
        })
    return lineloads


def prepare_loads(loads, nodes, hinges, elements, dof_to_node):
    forces = prepare_forces(loads, nodes, dof_to_node)
    moments = prepare_moments(loads, nodes, hinges, dof_to_node)
    lineloads = prepare_lineloads(loads, elements)
    return forces, moments, lineloads


def calculate_scale_factors(nodes, max_width_cm=15, max_height_cm=4):
    x_values = [node['x'] for node in nodes]
    y_values = [node['y'] for node in nodes]
    x_range = max(x_values) - min(x_values)
    y_range = max(y_values) - min(y_values)
    x_scale = max_width_cm / x_range if x_range != 0 else 1
    y_scale = max_height_cm / y_range if y_range != 0 else 1
    return x_scale, y_scale


def prepare_data_for_latex(beam_version: str, simulation_index, geometry, element_properties, loads):
    nodes, hinges, dof_to_node = prepare_nodes_hinges_and_dof_mapping(geometry)
    elements = prepare_elements(geometry, dof_to_node)
    supports = determine_supports(geometry, nodes, dof_to_node)
    forces, moments, lineloads = prepare_loads(loads, nodes, hinges, elements, dof_to_node)

    materials = [f"{ep['material']['E'] / 1_000_000:.0f}" for ep in element_properties]
    inertias = [f"{ep['section']['I']:.0f}" for ep in element_properties]
    lengths = []
    for element in elements:
        start_node = next(node for node in nodes if node['name'] == element['start'])
        end_node = next(node for node in nodes if node['name'] == element['end'])
        length = end_node['x'] - start_node['x']
        lengths.append(f"{length:.0f}")

    max_width_cm = 15
    x_scale, y_scale = calculate_scale_factors(nodes, max_width_cm)

    return {
        'beam_version': re.findall("\d+", beam_version)[0],
        'simulation_index': f'{simulation_index:03}',
        'nels': len(elements),
        'hinges': hinges,
        'nodes': nodes,
        'elements': elements,
        'supports': supports,
        'forces': forces,
        'moments': moments,
        'lineloads': lineloads,
        'materials': materials,
        'inertias': inertias,
        'lengths': lengths,
        'x_scale': x_scale,
        'y_scale': y_scale
    }


if __name__ == '__main__':
    beam_version = 'beam999'
    simulation_index = f'{1:03}'

    geometry = {'coord': [[0, 0], [3, 0], [3, 0], [6, 0], [9, 0], [12, 0]],
     'dof': [[1, 2, 3], [4, 5, 6], [4, 5, 16], [7, 8, 9], [10, 11, 12], [13, 14, 15]],
     'edof': [[1, 2, 3, 4, 5, 6], [4, 5, 16, 7, 8, 9], [7, 8, 9, 10, 11, 12], [10, 11, 12, 13, 14, 15]],
     'bc': [1, 2, 3, 8, 15], 'ndofs': 16, 'nels': 4}

    element_properties = [
        {'material': {'type': 'concrete', 'E': 30000000.0}, 'section': {'type': 'square20', 'A': 400, 'I': 13333.3}},
        {'material': {'type': 'concrete', 'E': 30000000.0}, 'section': {'type': 'square20', 'A': 400, 'I': 13333.3}},
        {'material': {'type': 'concrete', 'E': 30000000.0}, 'section': {'type': 'square20', 'A': 400, 'I': 13333.3}},
        {'material': {'type': 'concrete', 'E': 30000000.0}, 'section': {'type': 'square20', 'A': 400, 'I': 13333.3}}
    ]

    loads = {'P': 5, 'P_loc': 4, 'M': 1, 'M_loc': 15, 'q': [-2], 'q_loc': [3]}

    # data = {
    #     'nels': 6,
    #     'beam_version': '1',
    #     'simulation_index': f'{1:03}',
    #     'lengths': [f'{x:.0f}' for x in [3.0, 4.0, 5.0, 6.0, 7.0, 8.0]],
    #     'materials': [f"{x:.0f}" for x in [200, 200, 70, 50, 30, 12]],
    #     'inertia': [f"{x:.0f}" for x in [1000, 2000, 3000, 4000, 5000, 6000]],
    #     'load': {'P': f"{50:.0f}", 'M': f"{20:.0f}", 'q': f"{-10:.0f}"}
    # }

    data = prepare_data_for_latex(beam_version, simulation_index, geometry, element_properties, loads)

    generate_beam_pdf("beam_template.tex", "output_beam_report", data)
