# plane2d_generator.py
import random

import numpy as np

from .plane2d_solver import load_plane2d_configuration


def scale_plane_points(
    points: list,
    mesh_props: dict,
    min_scale: float = 1.0,
    max_scale: float = 2.0,
    step: float = 0.1,
):
    """
    Randomly select scale factors in x and y from the range [min_scale, max_scale] with given step.
    Returns the scaled points as a numpy array.
    """
    scale_options = np.arange(min_scale, max_scale + step, step)
    scale_x = random.choice(scale_options)
    scale_y = random.choice(scale_options)
    scaled = [[x * scale_x, y * scale_y] for x, y in points]
    max_scale = max(scale_x, scale_y)
    mesh_props["el_size_factor"] = mesh_props["el_size_factor"] * max_scale
    return np.array(scaled), mesh_props


def compute_max_dimensions(points: np.ndarray):
    """
    Given a set of points, returns (max_x, max_y).
    """
    xs = points[:, 0]
    ys = points[:, 1]
    return np.max(xs), np.max(ys)


def select_ptype_and_calculate_t(max_x: float, max_y: float):
    """
    Randomly choose ptype (1 or 2) and calculate thickness t.
    If ptype==1 (plane stress): t = min(max_x, max_y) / 10.
    If ptype==2 (plane strain): t = max(max_x, max_y) * 20.
    """
    ptype = random.choice([1, 2])
    if ptype == 1:
        t = min(max_x, max_y) / 10.0
    else:
        t = max(max_x, max_y) * 10.0
    return ptype, t


def choose_random_material(material_options: dict):
    """
    Randomly select a material from the available material options.
    Returns the dictionary for the selected material.
    """
    material_key = random.choice(list(material_options.keys()))
    return material_options[material_key]


def construct_material_data(ptype: int, material: dict, t: float):
    """
    Construct material_data for plane2d.
    """
    return {"ptype": ptype, "E": material["E"], "nu": material["nu"], "t": t}


def select_random_forces_with_scaling(
    forces_options: dict,
    min_scale: float = 1.0,
    max_scale: float = 5.0,
    step: float = 0.1,
    ptype: int = 1,
):
    """
    Randomly assign random force values.
    """
    global_sign = random.choice([1, -1])
    scaling_options = np.arange(min_scale, max_scale + step, step)

    forces_options_keys = list(forces_options.keys())
    selected_forces_keys = random.sample(forces_options_keys, k=2)
    selected_forces = {}

    for key in selected_forces_keys:
        selected_forces[key] = forces_options[
            key
        ].copy()  # create a copy so that the initial dictionary is not changed
        scale_factor = 1
        if ptype == 1:
            scale_factor = global_sign * random.choice(scaling_options)
        elif ptype == 2:
            scale_factor = global_sign * random.choice(scaling_options) * 20
        new_value = selected_forces[key]["value"] * scale_factor
        selected_forces[key]["value"] = new_value

    return selected_forces


def generate_plane2d_input_random(properties: dict, plane_version: str):
    """
    Generate random input data for plane2d analysis. Currently boundary conditions are predefined.
    It follows the steps:
      1. Load basic configuration from properties.json.
      2. Randomly scale points.
      3. Compute max dimensions.
      4. Randomly select ptype and calculate t.
      5. Randomly select a material.
      6. Construct material_data.
      7. Randomly scale forces and select direction.
      8. Return all generated input data.

    Returns:
        coords: scaled points (np.array).
        elements: original elements (list) or edofs in a suitable format.
        material_data: dictionary.
        boundary_conditions: dictionary.
        forces: dictionary.
        mesh_props: dictionary.
    """
    (
        points,
        elements,
        material_options,
        boundary_conditions,
        forces_options,
        mesh_props,
    ) = load_plane2d_configuration(properties, plane_version, "random")

    # Scale points randomly
    scaled_points, mesh_props = scale_plane_points(
        points, mesh_props, min_scale=1.0, max_scale=2.0, step=0.1
    )
    # Get max dimensions
    max_x, max_y = compute_max_dimensions(scaled_points)
    # Randomly select ptype and compute t
    ptype, t = select_ptype_and_calculate_t(max_x, max_y)
    # Randomly select material
    chosen_material = choose_random_material(material_options)
    # Construct material_data
    material_data = construct_material_data(ptype, chosen_material, t)
    # Select random forces
    forces = select_random_forces_with_scaling(forces_options, ptype=ptype)

    # You may want to store the scaled mesh in mesh_props or update the points.
    # Assume mesh_props are unchanged.
    return (
        scaled_points.tolist(),
        elements,
        material_data,
        boundary_conditions,
        forces,
        mesh_props,
    )
