# plane2d_plotter.py
import os

# CalFEM for Python
import calfem.core as cfc
import calfem.vis_mpl as cfv
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.transforms as mtransforms
import numpy as np
from matplotlib.patches import Circle, Rectangle
from matplotlib.path import Path

from .config import CM_TO_IN, results_dir, temp_dir

# Set global font properties:
mpl.rcParams.update(
    {
        "font.family": "serif",
        "font.serif": ["Liberation Serif", "Nimbus Roman", "Times New Roman"],
        "font.size": 10,
    }
)


def plot_plane2d_stresses(
    coords,
    edofs,
    dofs_per_node,
    el_type,
    es,
    component="sx",
    sim_data=None,
    mesh_name="predef",
):
    """
    Plot and save stress contour for either 'sx' or 'sy'.

    Parameters
    ----------
    coords : ndarray (n_nodes, 2)
        Node coords.
    edofs : ndarray (n_elements, n_dofs_per_el)
        Element topology (global DOFs).
    dofs_per_node : int
        e.g. 2
    el_type : int
        e.g. 2 => triangular elements
    es : ndarray (n_elements, 3)
        es[i] => [sx, sy, txy], typically in Pa
    component : str
        'sx' => index 0, 'sy' => index 1
    sim_data : tuple/list
        e.g. (mode, plane2d_version, simulation_index)
    mesh_name : str
        'predef' or 'auto' to distinguish filenames.

    Returns
    -------
    plot_path : str
        Path to the saved PDF figure.
    """
    # 1) pick the index for the requested component
    idx = 0 if component == "sx" else 1
    stress_component = es[:, idx]

    # 2) Convert to e.g. MPa
    stress_MPa = stress_component / 1e3  # convert kPa to MPa

    # 3) Prepare a figure
    cfv.figure(fig_size=(16, 8))

    # 4) Draw the stress as element values
    cfv.draw_element_values(
        stress_MPa,
        coords,
        edofs,
        dofs_per_node,
        el_type,
        displacements=None,
        draw_elements=False,
        draw_undisplaced_mesh=False,
        title=f"{component} [MPa] - {mesh_name}",
    )
    cfv.colorbar(shrink=0.35)

    # 5) Save figure
    if sim_data is not None:
        # unpack e.g. (mode, plane2d_version, simulation_index)
        mode, plane2d_version, simulation_index = sim_data
        fname = f"{mode}_{plane2d_version}_{simulation_index}_{mesh_name}_{component}.pdf"
    else:
        fname = f"{mesh_name}_{component}.pdf"

    plot_path = os.path.join(results_dir(), fname)
    plt.savefig(plot_path, bbox_inches="tight")
    plt.close()
    return plot_path


def plot_plane2d_displacement(
    coords,
    dofs,
    element_nodes,
    a,
    dofs_per_node,
    el_type,
    component="ux",
    sim_data=None,
    mesh_name="predef",
):
    """
    Plot and save nodal displacement contour (ux or vy) in millimeters.

    Parameters
    ----------
    coords : ndarray (n_nodes, 2)
        Node coordinates.
    dofs : ndarray (n_nodes, 2)
        dofs[i,0] => global x-DOF index (1-based)
        dofs[i,1] => global y-DOF index (1-based)
    element_nodes : ndarray (n_elements, n_nodes_per_el)
        Element topology .
    a : ndarray (n_dofs, 1)
        The global displacement vector.
    dofs_per_node : int
        Typically 2 for plane problems.
    el_type : int
        2 => triangular elements, etc.
    component : str
        'ux' => horizontal displacement, 'vy' => vertical displacement.
    sim_data : tuple or list
        e.g. [mode, plane2d_version, simulation_index]
    mesh_name : str
        'predef' or 'auto' for labeling the figure or filename.

    Returns
    -------
    plot_path : str
        File path to the saved PDF figure.
    """
    # 1) Figure out which dof-index we want
    idx = 0 if component == "ux" else 1  # 0 => x-DOF, 1 => y-DOF

    # 2) Convert from meters to millimeters
    #    a is shape (n_dofs,1).  For node i => dofs[i,idx]-1 => index in a.
    #    We'll produce a nodal field of shape (n_nodes,)
    disp_mm = []
    for i_node in range(coords.shape[0]):
        # get the global dof index for this node in the desired direction
        global_dof = dofs[i_node, idx] - 1  # 1-based => 0-based
        disp_mm.append(a[global_dof, 0] * 1000.0)  # convert to mm

    disp_mm = np.array(disp_mm)

    # 3) Build a figure
    cfv.figure(fig_size=(16, 8))

    # 4) Draw the nodal displacement contour
    cfv.draw_nodal_values(
        disp_mm,  # per-node field
        coords,  # node coords
        element_nodes,
        dofs_per_node=dofs_per_node,  # e.g. 2
        el_type=el_type,
        title=f"{component} [mm] - {mesh_name}",
    )
    cfv.colorbar(shrink=0.35)

    # 5) Construct output filename
    if sim_data is not None:
        mode, plane2d_version, simulation_index = sim_data
        # e.g. random_plane2_0_predef_ux.pdf
        fname = f"{mode}_{plane2d_version}_{simulation_index}_{mesh_name}_{component}.pdf"
    else:
        fname = f"{mesh_name}_{component}.pdf"

    plot_path = os.path.join(results_dir(), fname)
    plt.savefig(plot_path, bbox_inches="tight")
    plt.close()
    return plot_path


def draw_node_numbers(ax, coords, shape_path, font_size=10, color="black"):
    circle_radius_pts = 6.5
    base_offset_x_pts = 11.0
    base_offset_y_pts = 11.0

    offsets_candidates = [
        (-base_offset_x_pts, -base_offset_y_pts),  # top-left
        (+base_offset_x_pts, -base_offset_y_pts),  # top-right
        (-base_offset_x_pts, +base_offset_y_pts),  # bottom-left
        (+base_offset_x_pts, +base_offset_y_pts),  # bottom-right
    ]

    fontdict = {"family": "serif", "size": font_size, "color": color}

    text_objects = []
    legend_texts = ["Współrzędne:"]

    for i, (x, y) in enumerate(coords):
        node_id = i + 1
        chosen_offset = None
        for dx, dy in offsets_candidates:
            # Transform: place circle center at data coords (x,y) plus a display offset (dx,dy)
            test_transform = mtransforms.ScaledTranslation(
                x, y, ax.transData
            ) + mtransforms.ScaledTranslation(
                dx / ax.figure.dpi, dy / ax.figure.dpi, ax.figure.dpi_scale_trans
            )
            disp_center = test_transform.transform((0, 0))  # => display coords
            data_center = ax.transData.inverted().transform(disp_center)
            (cx_data, cy_data) = data_center
            if not shape_path.contains_point((cx_data, cy_data)):
                chosen_offset = (dx, dy)
                break

        if chosen_offset is None:
            chosen_offset = offsets_candidates[0]
            print(
                f"Warning: Node {node_id} cannot find offset outside polygon. Using top-left anyway."
            )

        dx, dy = chosen_offset
        transform = mtransforms.ScaledTranslation(
            x, y, ax.transData
        ) + mtransforms.ScaledTranslation(
            dx / ax.figure.dpi, dy / ax.figure.dpi, ax.figure.dpi_scale_trans
        )

        circle_patch = Circle(
            (0, 0),
            radius=circle_radius_pts,
            facecolor="white",
            edgecolor="black",
            linewidth=0.5,
            alpha=0.9,
            transform=transform,
            zorder=4,
        )
        circle_patch.set_clip_on(False)
        ax.add_patch(circle_patch)

        text_obj = ax.text(
            0,
            0,
            str(node_id),
            ha="center",
            va="center",
            fontdict=fontdict,
            transform=transform,
            zorder=5,
        )
        text_objects.append(text_obj)

        # For external listing
        x_str = f"{x:.2f}"
        y_str = f"{y:.2f}"
        legend_texts.append(f"{node_id}: ({x_str}, {y_str})")

    return legend_texts, text_objects


def draw_element_numbers(ax, ex, ey, font_size=10, color="black"):
    """
    Draw each element number at the element centroid, with a small rectangle
    in display coordinates so it won't scale with data.
    """
    rect_width_pts = 11.5
    rect_height_pts = 11.0

    fontdict = {"family": "serif", "size": font_size, "color": color}

    text_objects = []
    for i in range(ex.shape[0]):
        cx = np.mean(ex[i])
        cy = np.mean(ey[i])
        elem_id = i + 1

        transform = mtransforms.ScaledTranslation(cx, cy, ax.transData)

        rect_patch = Rectangle(
            xy=(-rect_width_pts / 2, -rect_height_pts / 2),
            width=rect_width_pts,
            height=rect_height_pts,
            facecolor="white",
            edgecolor="black",
            linewidth=0.5,
            alpha=0.9,
            zorder=4,
            transform=transform,
        )
        rect_patch.set_clip_on(False)
        ax.add_patch(rect_patch)

        elem_obj = ax.text(
            0,
            0,
            str(elem_id),
            ha="center",
            va="center",
            fontdict=fontdict,
            transform=transform,
            zorder=5,
        )
        text_objects.append(elem_obj)

    return text_objects


def plot_predefined_mesh(coords, dofs, edofs, mesh_props, simulation_data):
    """
    Plot the predefined mesh (16x6 cm), minimal whitespace, aspect=1,
    circles and rectangles in display coords, node coords listed to right.
    """
    dofs_per_node = mesh_props["dofs_per_node"]
    el_type = mesh_props["el_type"]
    ex, ey = cfc.coordxtr(edofs, coords, dofs)
    shape_path = Path(coords, closed=True)

    # Figure size: 16 cm x 6 cm
    fig, ax = plt.subplots(figsize=(16 * CM_TO_IN, 6 * CM_TO_IN))

    # Draw mesh
    cfv.draw_mesh(
        coords,
        edofs,
        dofs_per_node,
        el_type,
        filled=True,
        face_color=(0.875, 0.875, 0.875),
    )
    cfv.draw_node_circles(ex, ey, filled=True, marker_type=".")

    # Node & element numbers
    legend_texts, node_texts = draw_node_numbers(
        ax, coords, shape_path, font_size=10, color="black"
    )
    _ = draw_element_numbers(ax, ex, ey, font_size=10, color="black")

    # Force aspect ratio 1 and remove selected spines
    ax.set_aspect("equal", adjustable="datalim")
    ax.spines[["right", "top"]].set_visible(False)

    # Show node coords externally
    node_info = "\n".join(legend_texts)
    fig.text(0.82, 0.5, node_info, ha="left", va="center", fontsize=10)

    # Subplot margins => minimal whitespace
    # Enough left & bottom for axes labels, enough right for text
    plt.subplots_adjust(left=0.1, right=0.8, top=0.93, bottom=0.1)

    # Save with bbox_inches='tight' to remove extra page margin
    plane2d_version, simulation_index, plot_type = simulation_data
    plot_filename = f"{plane2d_version}_{simulation_index}_{plot_type}.pdf"
    plot_path = os.path.join(temp_dir(), plot_filename)
    os.makedirs(os.path.dirname(plot_path), exist_ok=True)
    fig.savefig(plot_path, format="pdf", bbox_inches="tight")
    plt.close(fig)
    return plot_path


def plot_auto_mesh(coords, edofs, mesh_props, simulation_data):
    dofs_per_node = mesh_props["dofs_per_node"]
    el_type = mesh_props["el_type"]
    fig, ax = plt.subplots(figsize=(16 * CM_TO_IN, 8 * CM_TO_IN))
    cfv.draw_mesh(coords, edofs, dofs_per_node, el_type=el_type, filled=True)

    # Save figure
    plot_filename = "{}_{}_{}_mesh_auto.pdf".format(*simulation_data)
    plot_path = os.path.join(results_dir(), plot_filename)
    os.makedirs(os.path.dirname(plot_path), exist_ok=True)
    fig.savefig(plot_path, format="pdf", bbox_inches="tight")
    plt.close(fig)
