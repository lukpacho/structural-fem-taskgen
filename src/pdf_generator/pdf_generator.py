import subprocess
import os
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
        autoescape=False,
        loader=FileSystemLoader(searchpath=template_folder)
    )


def render_latex_template(template_file, output_name, data):
    template_env = latex_jinja_env()
    template = template_env.get_template(template_file)

    output_text = template.render(data)
    with open(os.path.join(TEMP_DIR, f'{output_name}.tex'), "w") as text_file:
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
    os.rename(os.path.join(TEMP_DIR, pdf_file), os.path.join(PDFS_DIR, pdf_file))
    os.rename(os.path.join(TEMP_DIR, f"{output_name}.tex"), os.path.join(PDFS_DIR, f"{output_name}.tex"))

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

    data = {
        'nels': 6,
        'beam_version': '1',
        'simulation_index': f'{1:03}',
        'lengths': [f'{x:.0f}' for x in [3.0, 4.0, 5.0, 6.0, 7.0, 8.0]],
        'materials': [f"{x:.0f}" for x in [200, 200, 70, 50, 30, 12]],
        'inertia': [f"{x:.0f}" for x in [1000, 2000, 3000, 4000, 5000, 6000]],
        'load': {'P': f"{50:.0f}", 'M': f"{20:.0f}", 'q': f"{-10:.0f}"}
    }
    generate_beam_pdf("beam_template.tex", "output_beam_report", data)
