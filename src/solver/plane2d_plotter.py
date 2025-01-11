import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.patches import Circle, Rectangle

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


def draw_node_numbers(ax, coords, color='black'):
    """
    Draw node numbering at each (x,y) in coords.
    The number is drawn on top of a small white circular patch.

    Parameters:
        ax      : matplotlib.axes instance where text and patches are drawn.
        coords  : np.array of shape (n_nodes, 2) containing (x,y) positions.
        color   : color for the text.
    """
    offset_x = 0.09
    offset_y = 0.09
    # Define a font dict (though rcParams already set the global font)
    fontdict = {'family': 'Times New Roman', 'size': 10, 'color': color}
    # Set the circle radius (adjust as needed)
    radius = 0.075
    for i, (x, y) in enumerate(coords):
        # Create and add a circular patch (the background for the node number)
        circle = Circle((x + offset_x, y + offset_y), radius=radius,
                        facecolor='white', edgecolor='black', linewidth=0.25,
                        alpha=0.8, zorder=4)
        ax.add_patch(circle)
        # Draw the node number text
        ax.text(x + offset_x, y + offset_y, str(i + 1),
                ha='center', va='center', fontdict=fontdict, zorder=5)


def draw_element_numbers(ax, ex, ey, color='black'):
    """
    Draw element numbering near each element's centroid.
    The number is drawn on top of a small white rectangular patch.

    Parameters:
        ax      : matplotlib.axes instance where text and patches are drawn.
        ex, ey  : arrays of shape (n_elements, n_nodes_per_element) with element coordinates.
        color   : color for the text.
    """
    fontdict = {'family': 'Times New Roman', 'size': 10, 'color': color}
    # Define the rectangle dimensions (adjust these values if needed)
    rect_width = 0.11
    rect_height = 0.12
    for i in range(ex.shape[0]):
        cx = np.mean(ex[i])
        cy = np.mean(ey[i])
        # Draw a rectangle patch centered at (cx,cy)
        rect = Rectangle((cx - rect_width/2, cy - rect_height/2),
                         width=rect_width, height=rect_height,
                         facecolor='white', edgecolor='black', linewidth=0.25,
                         alpha=0.8, zorder=4)
        ax.add_patch(rect)
        # Draw the element number text
        ax.text(cx, cy, str(i + 1),
                ha='center', va='center', fontdict=fontdict, zorder=5)


def plot_predefined_mesh(coords, dofs, edofs, mesh_props, simulation_data):
    """
    Plot the predefined mesh and overlay node and element numbering.
    The figure is sized so that its width is 16 cm maximum.

    Parameters:
       coords         : np.array of node coordinates.
       dofs           : np.array of DOFs.
       edofs          : np.array of element DOFs.
       mesh_props     : dict containing, e.g., 'dofs_per_node' and 'el_type'.
       simulation_data: tuple, e.g. (plane2d_version, simulation_index, plot_type).

    Returns:
       plot_path: The full path to the saved plot.
    """
    dofs_per_node = mesh_props['dofs_per_node']
    el_type = mesh_props['el_type']
    ex, ey = cfc.coordxtr(edofs, coords, dofs)

    # Create the figure with a max width of 16 cm; height is chosen to preserve aspect
    fig, ax = plt.subplots(figsize=(16 * cm_to_in, 6 * cm_to_in))

    # Draw mesh using CalFEM functions
    cfv.draw_mesh(coords, edofs, dofs_per_node, el_type, filled=True, face_color=(0.85, 0.85, 0.85))
    cfv.draw_node_circles(ex, ey, filled=True, marker_type='.')

    # Draw node and element numbers
    draw_node_numbers(ax, coords, color='black')
    draw_element_numbers(ax, ex, ey, color='black')

    # Turn off top and right axes spines
    for spine in ['top', 'right', 'bottom', 'left']:
        ax.spines[spine].set_visible(False)
    ax.tick_params(top=False, right=False)

    # Compute data limits.
    xmin, xmax = ax.get_xlim()
    ymin, ymax = ax.get_ylim()

    # Add arrows on the bottom (x-axis) and left (y-axis) in data coordinates.
    offset = 0.025
    ax.annotate('', xy=(xmax, ymin), xycoords='data',
                xytext=(xmin - offset, ymin), textcoords='data',
                arrowprops=dict(arrowstyle="->", color='black', lw=0.5))
    ax.annotate('', xy=(xmin, ymax), xycoords='data',
                xytext=(xmin, ymin - offset), textcoords='data',
                arrowprops=dict(arrowstyle="->", color='black', lw=0.5))

    # Adjust subplot margins to remove excess white space above without rescaling.
    plt.subplots_adjust(top=0.95, right=0.98, left=0.15, bottom=0.15)

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