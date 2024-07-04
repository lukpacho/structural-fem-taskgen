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


def prepare_nodes_and_hinges(geometry):
    coord_to_node = {}
    nodes = []
    hinges = []
    for idx, coord in enumerate(geometry['coord']):
        coord_tuple = tuple(coord)
        if coord_tuple in coord_to_node:
            if coord_tuple not in hinges:
                hinges.append(coord_to_node[coord_tuple])
        else:
            node_name = f'n{len(nodes) + 1}'
            nodes.append({'name': node_name, 'x': coord[0], 'y': coord[1]})
            coord_to_node[coord_tuple] = node_name

    return nodes, hinges


def prepare_elements(nodes):
    elements = []
    for i in range(len(nodes) - 1):
        elements.append({'start': nodes[i]['name'], 'end': nodes[i + 1]['name']})
    return elements


def determine_supports(geometry, nodes):
    support_types = {
        1: ('floating bearing', 2),
        2: ('fixed bearing', 1),
        3: ('fixed support', 3)
    }
    node_supports = {}

    # Initialize support records for each boundary condition
    for bc in geometry['bc']:
        node_idx = (bc - 1) // 3
        node_name = nodes[node_idx]['name']
        if node_name not in node_supports:
            node_supports[node_name] = set()
        node_supports[node_name].add((bc - 1) % 3)

    # Determine the type of support based on the number of dofs constrained
    supports = []
    last_node_name = nodes[-1]['name']
    for node, dofs in node_supports.items():
        if len(dofs) in support_types:
            support_type, type_number = support_types[len(dofs)]
            if support_type == 'fixed support':
                if node == 'n1':
                    rotation = -90
                elif node == last_node_name:
                    rotation = 90
            else:
                rotation = 0
            supports.append({'node': node, 'type': support_type, 'type_number': type_number, 'rotation': rotation})
        else:
            print(f"Warning: Unsupported number of constraints ({len(dofs)}) at node {node}")

    return supports


def prepare_forces(loads, nodes):
    forces = []
    if 'P' in loads:
        node_idx = (loads['P_loc'] - 1) // 3  # Assuming each node has 3 dofs
        node_name = nodes[node_idx]['name']
        rotation = -90 if loads['P'] > 0 else 90
        forces.append({
            'node': node_name,
            'type': 'point',
            'magnitude': abs(loads['P']),
            'rotation': rotation,
            'length': 1.5,
            'distance': 0.05
        })
    return forces


def prepare_moments(loads, nodes):
    moments = []
    if 'M' in loads:
        node_idx = (loads['M_loc'] - 1) // 3
        node_name = nodes[node_idx]['name']
        orientation = 3 if loads['M'] > 0 else 2  # 2 for clockwise, 3 for counterclockwise
        moments.append({
            'node': node_name,
            'orientation': orientation,
            'magnitude': abs(loads['M']),
            'rotation': 10,
            'angle': 200,
            'distance': 0.5
        })
    return moments


def prepare_lineloads(loads, elements):
    lineloads = []
    for q_val, q_range in zip(loads['q'], loads['q_loc']):
        start_node = elements[q_range]['start']
        end_node = elements[q_range]['end']
        value = -0.35 if q_val > 0 else 0.35
        lineloads.append({
            'node1': start_node,
            'node2': end_node,
            'type': 'distributed',
            'value': value,
            'magnitude': q_val
        })
    return lineloads


def prepare_loads(loads, nodes, elements):
    forces = prepare_forces(loads, nodes)
    moments = prepare_moments(loads, nodes)
    lineloads = prepare_lineloads(loads, elements)
    return forces, moments, lineloads


def prepare_data_for_latex(beam_version: str, simulation_index, geometry, element_properties, loads):
    nodes, hinges = prepare_nodes_and_hinges(geometry)
    elements = prepare_elements(nodes)
    supports = determine_supports(geometry, nodes)
    forces, moments, lineloads = prepare_loads(loads, nodes, elements)

    materials = [f"{ep['material']['E']/1_000_000:.0f}" for ep in element_properties]
    inertias = [f"{ep['section']['I']:.0f}" for ep in element_properties]
    lengths = [f"{nodes[i + 1]['x'] - nodes[i]['x']:.0f}" for i in range(geometry['nels'])]

    return {
        'beam_version': re.findall("\d+", beam_version)[0], 'simulation_index': f'{simulation_index:03}',
        'nels': geometry['nels'], 'hinges': hinges, 'nodes': nodes, 'elements': elements,
        'supports': supports, 'forces': forces, 'moments': moments, 'lineloads': lineloads,
        'materials': materials, 'inertias': inertias, 'lengths': lengths
    }


if __name__ == '__main__':
    beam_version = 'beam999'
    simulation_index = f'{1:03}'

    geometry = {'coord': [[0, 0], [3, 0], [3, 0], [6, 0], [9, 0], [12, 0]],
     'dof': [[1, 2, 3], [4, 5, 6], [4, 5, 16], [7, 8, 9], [10, 11, 12], [13, 14, 15]],
     'edof': [[1, 2, 3, 4, 5, 6], [4, 5, 16, 7, 8, 9], [7, 8, 9, 10, 11, 12], [10, 11, 12, 13, 14, 15]],
     'bc': [1, 2, 3, 8, 14], 'ndofs': 16, 'nels': 4}

    element_properties = [
        {'material': {'type': 'concrete', 'E': 30000000.0}, 'section': {'type': 'square20', 'A': 400, 'I': 13333.3}},
        {'material': {'type': 'concrete', 'E': 30000000.0}, 'section': {'type': 'square20', 'A': 400, 'I': 13333.3}},
        {'material': {'type': 'concrete', 'E': 30000000.0}, 'section': {'type': 'square20', 'A': 400, 'I': 13333.3}},
        {'material': {'type': 'concrete', 'E': 30000000.0}, 'section': {'type': 'square20', 'A': 400, 'I': 13333.3}}
    ]

    loads = {'P': 5, 'P_loc': 4, 'q': [-2, -2], 'q_loc': [2, 3]}

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
