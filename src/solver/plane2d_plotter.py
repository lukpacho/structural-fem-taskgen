import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib.transforms as mtransforms
from matplotlib.patches import Circle, Rectangle
from matplotlib.path import Path
from adjustText import adjust_text

# CalFEM for Python
import calfem.core as cfc
import calfem.geometry as cfg
import calfem.mesh as cfm
import calfem.vis_mpl as cfv

from config import BASE_DIR, cm_to_in

# Set global font properties: Times New Roman, size 10.
mpl.rcParams['font.family'] = 'Times New Roman'
mpl.rcParams['font.size'] = 10

def plot_plane2d_results():
    pass


def draw_node_numbers(ax, coords, shape_path, font_size=10, color='black'):
    circle_radius_pts = 6.5
    base_offset_x_pts = 12.0
    base_offset_y_pts = 11.0

    offsets_candidates = [
        (-base_offset_x_pts, -base_offset_y_pts),  # top-left
        (+base_offset_x_pts, -base_offset_y_pts),  # top-right
        (-base_offset_x_pts, +base_offset_y_pts),  # bottom-left
        (+base_offset_x_pts, +base_offset_y_pts),  # bottom-right
    ]

    fontdict = {'family': 'Times New Roman', 'size': font_size, 'color': color}

    text_objects = []
    legend_texts = ['Współrzędne:']

    for i, (x, y) in enumerate(coords):
        node_id = i + 1
        chosen_offset = None
        for (dx, dy) in offsets_candidates:
            # Transform: place circle center at data coords (x,y) plus a display offset (dx,dy)
            transform_test = (
                    mtransforms.ScaledTranslation(x, y, ax.transData)
                    + mtransforms.ScaledTranslation(
                dx / ax.figure.dpi,
                dy / ax.figure.dpi,
                ax.figure.dpi_scale_trans
                )
            )
            disp_center = transform_test.transform((0, 0))  # => display coords
            data_center = ax.transData.inverted().transform(disp_center)
            (cx_data, cy_data) = data_center
            if not shape_path.contains_point((cx_data, cy_data)):
                chosen_offset = (dx, dy)
                break

        if chosen_offset is None:
            chosen_offset = offsets_candidates[0]
            print(f"Warning: Node {node_id} cannot find offset outside polygon. Using top-left anyway.")

        dx, dy = chosen_offset
        transform = (
                mtransforms.ScaledTranslation(x, y, ax.transData)
                + mtransforms.ScaledTranslation(
            dx / ax.figure.dpi,
            dy / ax.figure.dpi,
            ax.figure.dpi_scale_trans
            )
        )

        circle_patch = Circle(
            (0, 0),
            radius=circle_radius_pts,
            facecolor='white',
            edgecolor='black',
            linewidth=0.5,
            alpha=0.9,
            transform=transform,
            zorder=4
        )
        circle_patch.set_clip_on(False)
        ax.add_patch(circle_patch)

        text_obj = ax.text(
            0, 0, str(node_id),
            ha='center', va='center',
            fontdict=fontdict,
            transform=transform,
            zorder=5
        )
        text_objects.append(text_obj)

        # For external listing
        x_str = f"{x:.2f}"
        y_str = f"{y:.2f}"
        legend_texts.append(f"{node_id}: ({x_str}, {y_str})")

    return legend_texts, text_objects


def draw_element_numbers(ax, ex, ey, font_size=10, color='black'):
    """
    Draw each element number at the element centroid, with a small rectangle
    in display coordinates so it won't scale with data.
    """
    rect_width_pts = 11.5
    rect_height_pts = 11.0

    fontdict = {'family': 'Times New Roman', 'size': font_size, 'color': color}

    text_objects = []
    for i in range(ex.shape[0]):
        cx = np.mean(ex[i])
        cy = np.mean(ey[i])
        elem_id = i + 1

        transform = mtransforms.ScaledTranslation(cx, cy, ax.transData)

        rect_patch = Rectangle(
            xy=(-rect_width_pts/2, -rect_height_pts/2),
            width=rect_width_pts, height=rect_height_pts,
            facecolor='white', edgecolor='black', linewidth=0.5,
            alpha=0.9, zorder=4,
            transform=transform
        )
        rect_patch.set_clip_on(False)
        ax.add_patch(rect_patch)

        elem_obj = ax.text(
            0, 0, str(elem_id),
            ha='center', va='center',
            fontdict=fontdict,
            transform=transform,
            zorder=5
        )
        text_objects.append(elem_obj)

    return text_objects


def plot_predefined_mesh(coords, dofs, edofs, mesh_props, simulation_data):
    """
    Plot the predefined mesh (16x6 cm), minimal whitespace, aspect=1,
    circles and rectangles in display coords, node coords listed to right.
    """
    dofs_per_node = mesh_props['dofs_per_node']
    el_type = mesh_props['el_type']
    ex, ey = cfc.coordxtr(edofs, coords, dofs)
    shape_path = Path(coords, closed=True)

    # Figure size: 16 cm x 6 cm
    fig, ax = plt.subplots(figsize=(16 * cm_to_in, 6 * cm_to_in))

    # Draw mesh
    cfv.draw_mesh(coords, edofs, dofs_per_node, el_type, filled=True, face_color=(0.875, 0.875, 0.875))
    cfv.draw_node_circles(ex, ey, filled=True, marker_type='.')

    # Node & element numbers
    legend_texts, node_texts = draw_node_numbers(ax, coords, shape_path, font_size=10, color='black')
    elem_texts = draw_element_numbers(ax, ex, ey, font_size=10, color='black')

    # Force aspect ratio 1 and remove selected spines
    ax.set_aspect('equal', adjustable='datalim')
    ax.spines[['right', 'top']].set_visible(False)

    # Show node coords externally
    node_info = "\n".join(legend_texts)
    fig.text(0.82, 0.5, node_info, ha='left', va='center', fontsize=10)

    # Subplot margins => minimal whitespace
    # Enough left & bottom for axes labels, enough right for text
    plt.subplots_adjust(left=0.1, right=0.8, top=0.93, bottom=0.1)

    # Save with bbox_inches='tight' to remove extra page margin
    plane2d_version, simulation_index, plot_type = simulation_data
    plot_filename = f"{plane2d_version}_{simulation_index}_{plot_type}.pdf"
    plot_path = os.path.join(BASE_DIR, "data", "temp", plot_filename)
    fig.savefig(plot_path, format='pdf', bbox_inches='tight')
    plt.close(fig)
    return plot_path


def plot_auto_mesh(coords, edofs, mesh_props, simulation_data):
    dofs_per_node = mesh_props['dofs_per_node']
    el_type = mesh_props['el_type']
    fig, ax = plt.subplots(figsize=(16 * cm_to_in, 8 * cm_to_in))
    cfv.draw_mesh(coords, edofs, dofs_per_node, el_type=el_type, filled=True)

    # Save figure
    plot_filename = '{}_{}_{}_mesh_auto.pdf'.format(*simulation_data)
    plot_path = os.path.join(BASE_DIR, "data", "temp", plot_filename)
    fig.savefig(plot_path, format='pdf')
    plt.close(fig)