import os
import numpy as np
import matplotlib.pyplot as plt

# CalFEM for Python
import calfem.core as cfc
import calfem.geometry as cfg
import calfem.mesh as cfm
import calfem.vis_mpl as cfv

from config import BASE_DIR, cm_to_in

def plot_plane2d_results():
    pass


def draw_node_numbers(ax, coords, color='blue'):
    """
    Draw node numbering at each (x,y) in coords with a white-translucent box.
    """
    offset_x = 0.1
    offset_y = 0.1
    for i, (x, y) in enumerate(coords):
        ax.text(
            x + offset_x, y + offset_y, str(i + 1),
            color=color,
            ha='center', va='center',
            bbox=dict(facecolor='white', alpha=0.7, edgecolor='none'),
            zorder=5
        )


def draw_element_numbers(ax, ex, ey, color='red'):
    """
    Draw element numbering near each element's centroid with a white-translucent box.

    ex, ey shape: (n_elements, n_nodes_per_element)
    We'll label each element i with its index i+1 at the centroid.
    """
    for i in range(ex.shape[0]):
        cx = np.mean(ex[i])
        cy = np.mean(ey[i])
        ax.text(
            cx, cy, str(i + 1),
            color=color,
            ha='center', va='center',
            bbox=dict(facecolor='white', alpha=0.7, edgecolor='none'),
            zorder=5
        )


def plot_predefined_mesh(coords, dofs, edofs, mesh_props, simulation_data):
    dofs_per_node = mesh_props['dofs_per_node']
    el_type = mesh_props['el_type']

    ex, ey = cfc.coordxtr(edofs, coords, dofs)

    fig, ax = plt.subplots(figsize=(16 * cm_to_in, 8 * cm_to_in))
    cfv.draw_mesh(coords, edofs, dofs_per_node, el_type, filled=True)
    cfv.draw_node_circles(ex, ey, filled=True, marker_type='.')
    draw_node_numbers(ax, coords, color='blue')
    draw_element_numbers(ax, ex, ey, color='red')

    # Save figure
    plane2d_version, simulation_index, plot_type = simulation_data
    plot_filename = f"{plane2d_version}_{simulation_index}_{plot_type}.pdf"
    plot_path = os.path.join(BASE_DIR, "data", "temp", plot_filename)
    fig.savefig(plot_path, format='pdf')
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