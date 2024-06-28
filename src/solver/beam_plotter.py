from calfem.vis_mpl import *
from config import BASE_DIR, ANNOTATION_DISPLACEMENT_MINIMUM, ANNOTATION_THRESHOLD, cm, m_to_cm


def plot_beam_results(ex, ey, element_results, max_results, mode, beam_version, simulation_index=0):
    plt.rcParams.update({'font.size': 9})
    simulation_data = [mode, beam_version, simulation_index]
    # Define offsets
    # offset_x = ex.max()/20
    # offset_y = 2
    # limit_x = [-offset_x, ex.max()+offset_x]
    # limit_y = [-offset_y, ey.max()+offset_y]

    # Plot displacements
    fig, ax = plt.subplots(figsize=(16 * cm, 8 * cm))
    plot_beam_displacements(ax, ex, ey, element_results, max_results)
    manage_plot(simulation_data, fig, ax, 'Displacements, cm')

    # # Plot shear forces
    # axs[1].set_title('Shear Forces')
    # plot_beam_displacements(axs[0], ex, ey, element_results, max_results, limit_x, limit_y)
    # # plot_beam_shear_forces(axs[1], 'T', ex, ey, results, limits)
    #
    # # Plot moments
    # axs[2].set_title('Moments')
    # plot_beam_displacements(axs[0], ex, ey, element_results, max_results, limit_x, limit_y)
    # # plot_beam_moments(axs[2], 'M', ex, ey, results, limits)
    #
    # # Save the figures
    # plt.tight_layout()
    # plot_filename = f'{mode}_{beam_version}_{simulation_index}_results'
    # plot_path = os.path.join(BASE_DIR, 'data', 'results', plot_filename)
    # plt.savefig(plot_path + '.pdf')
    # # plt.savefig(plot_path + '.png', dpi=1200)
    # plt.show()


def plot_beam_displacements(ax, ex, ey, element_results, max_results):
    scale_factor = scalfact2(ex, ey, max_results['ed'], 0.3)
    ax.set_title('Displacements, cm')
    ax.axis('off')
    eldraw2(ex, ey, [2, 1, 0])  # Line type, line color, node mark

    # List to keep track of annotation coordinates to avoid overlaps
    annotation_positions = []

    for i, result in element_results.items():
        edi = result['edi']
        dispbeam2_ax(ax, ex[i], ey[i], edi, [1, 2, 3], scale_factor)

        annotate_displacement_values(ax, ex[i], ey[i], edi, scale_factor, annotation_positions)
        # annotate_extreme_values(ax, edi, ex[i], ey[i], scale_factor, annotation_positions)

        # # Node and midpoint annotations
        # for j in range(len(ex[i])):
        #     # Ensure to access scalar values for annotation
        #     displacement_value = edi[j, 1]  # Assuming edi is [N, 1] or [N, 2] and we need the first component
        #     pos_x, pos_y = ex[i][j], ey[i][j] + displacement_value * scale_factor
        #
        #     # Only annotate significant displacements and avoid zero
        #     if np.abs(displacement_value) > ANNOTATION_DISPLACEMENT_MINIMUM:
        #         if not any(np.sqrt((pos_x - x) ** 2 + (pos_y - y) ** 2) < ANNOTATION_THRESHOLD for x, y in annotation_positions):
        #             ax.annotate(f'{displacement_value*100:.2f}', xy=(pos_x, pos_y), textcoords="offset points",
        #                         xytext=(0, 10), ha='center')
        #             annotation_positions.append((pos_x, pos_y))
        #
        # # Additional midpoint or specific annotations
        # midpoint_idx = len(ex[i]) // 2
        # midpoint_x = (ex[i][0] + ex[i][-1]) / 2
        # midpoint_y = (ey[i][0] + ey[i][-1]) / 2 + edi[midpoint_idx, 0] * scale_factor
        # if not any(np.sqrt((midpoint_x - x) ** 2 + (midpoint_y - y) ** 2) < ANNOTATION_THRESHOLD for x, y in annotation_positions):
        #     ax.annotate(f'{edi[midpoint_idx, 1]*100:.2f}', xy=(midpoint_x, midpoint_y), textcoords="offset points",
        #                 xytext=(0, 10), ha='center')
        #     annotation_positions.append((midpoint_x, midpoint_y))


def annotate_displacement_values(ax, ex, ey, edi, scale_factor, annotation_positions):
    # Indices for start, mid, and end positions
    indices = [0, len(edi) // 2, -1]
    positions = [(ex[0], ey[0] + edi[0, 1] * scale_factor),
                 (np.mean([ex[0], ex[1]]), np.mean([ey[0], ey[1]]) + edi[len(edi) // 2, 1] * scale_factor),
                 (ex[1], ey[1] + edi[-1, 1] * scale_factor)]

    # Process each specified position for potential annotation
    for index, (pos_x, pos_y) in zip(indices, positions):
        displacement_value = edi[index, 1] * m_to_cm  # Convert displacement to cm
        # Check if the displacement is significant and not near other annotations
        if np.abs(displacement_value) > ANNOTATION_DISPLACEMENT_MINIMUM:
            if not is_near_other_annotations(pos_x, pos_y, annotation_positions):
                ax.annotate(f'{displacement_value:.2f}', xy=(pos_x, pos_y),
                            textcoords="offset points", xytext=(10, 20), ha='center', va='bottom',
                            arrowprops=dict(arrowstyle="->", connectionstyle="arc3", color='blue'),
                            bbox=dict(boxstyle="round,pad=0.5", facecolor='yellow', edgecolor='black', alpha=0.5))
                annotation_positions.append((pos_x, pos_y))


def is_near_other_annotations(x, y, positions, threshold=ANNOTATION_THRESHOLD):
    return any(np.sqrt((x - px) ** 2 + (y - py) ** 2) < threshold for px, py in positions)


def dispbeam2_ax(ax, ex, ey, edi, plotpar=[2, 1, 1], sfac=None):
    """
        dispbeam2(ex,ey,edi,plotpar,sfac)
        [sfac]=dispbeam2(ex,ey,edi)
        [sfac]=dispbeam2(ex,ey,edi,plotpar)
    ------------------------------------------------------------------------
        PURPOSE
        Draw the displacement diagram for a two dimensional beam element.

        INPUT:   ex = [ x1 x2 ]
                ey = [ y1 y2 ]	element node coordinates.

                edi = [ u1 v1;
                       u2 v2;
                                 .....] 	matrix containing the displacements
                                              in Nbr evaluation points along the beam.

                plotpar=[linetype, linecolour, nodemark]

                         linetype=1 -> solid   linecolour=1 -> black
                                  2 -> dashed             2 -> blue
                                  3 -> dotted             3 -> magenta
                                                         4 -> red
                         nodemark=0 -> no mark
                                  1 -> circle
                                  2 -> star
                                  3 -> point

                         sfac = [scalar] scale factor for displacements.

                Rem. Default if sfac and plotpar is left out is auto magnification
               and dashed black lines with circles at nodes -> plotpar=[1 1 1]
    ------------------------------------------------------------------------

        LAST MODIFIED: O Dahlblom  2015-11-18
                       O Dahlblom  2023-01-31 (Python)
                       O lukpacho  2024-06-06 (Modified to use ax instead of plt)

        Copyright (c)  Division of Structural Mechanics and
                       Division of Solid Mechanics.
                       Lund University
    ------------------------------------------------------------------------
    """
    if ex.shape != ey.shape:
        raise ValueError("Check size of ex, ey dimensions.")

    rows, cols = edi.shape
    if cols != 2:
        raise ValueError("Check size of edi dimension.")
    Nbr = rows

    x1, x2 = ex
    y1, y2 = ey
    dx = x2 - x1
    dy = y2 - y1
    L = np.sqrt(dx * dx + dy * dy)
    nxX = dx / L
    nyX = dy / L
    n = np.array([nxX, nyX])

    line_color, line_style, node_color, node_style = pltstyle2(plotpar)

    if sfac is None:
        sfac = (0.1 * L) / (np.max(abs(edi)))

    eci = np.arange(0.0, L + L / (Nbr - 1), L / (Nbr - 1)).reshape(Nbr, 1)

    edi1 = edi * sfac
    # From local x-coordinates to global coordinates of the beam element.
    A = np.zeros(2 * Nbr).reshape(Nbr, 2)
    A[0, 0] = ex[0]
    A[0, 1] = ey[0]
    for i in range(1, Nbr):
        A[i, 0] = A[0, 0] + eci[i] * n[0]
        A[i, 1] = A[0, 1] + eci[i] * n[1]

    for i in range(0, Nbr):
        A[i, 0] = A[i, 0] + edi1[i, 0] * n[0] - edi1[i, 1] * n[1]
        A[i, 1] = A[i, 1] + edi1[i, 0] * n[1] + edi1[i, 1] * n[0]
    xc = np.array(A[:, 0])
    yc = np.array(A[:, 1])

    ax.plot(xc, yc, color=line_color, linewidth=1)

    A1 = np.array([A[0, 0], A[Nbr - 1, 0]]).reshape(1, 2)
    A2 = np.array([A[0, 1], A[Nbr - 1, 1]]).reshape(1, 2)
    draw_node_circles_ax(ax, A1, A2, color=node_color, filled=False, marker_type=node_style)


def draw_node_circles_ax(ax, ex, ey, title="", color=(0, 0, 0), face_color=(0.8, 0.8, 0.8), filled=False, marker_type="o"):
    """
    Draws wire mesh of model in 2D or 3D. Returns the Mesh object that represents
    the mesh.
    Args:
        coords:
            An N-by-2 or N-by-3 array. Row i contains the x,y,z coordinates of node i.
        edof:
            An E-by-L array. Element topology. (E is the number of elements and L is the number of dofs per element)
        dofs_per_nodes:
            Integer. Dofs per node.
        el_type:
            Integer. Element Type. See Gmsh manual for details. Usually 2 for triangles or 3 for quadrangles.
        axes:
            Matplotlib Axes. The Axes where the model will be drawn. If unspecified the current Axes will be used, or a new Axes will be created if none exist.
        axes_adjust:
            Boolean. True if the view should be changed to show the whole model. Default True.
        title:
            String. Changes title of the figure. Default "Mesh".
        color:
            3-tuple or char. Color of the wire. Defaults to black (0,0,0). Can also be given as a character in 'rgbycmkw'.
        face_color:
            3-tuple or char. Color of the faces. Defaults to white (1,1,1). Parameter filled must be True or faces will not be drawn at all.
        filled:
            Boolean. Faces will be drawn if True. Otherwise only the wire is drawn. Default False.
    """

    nel = ex.shape[0]
    nnodes = ex.shape[1]

    nodes = []

    x = []
    y = []

    for elx, ely in zip(ex, ey):
        for xx, yy in zip(elx, ely):
            x.append(xx)
            y.append(yy)

    if filled:
        ax.scatter(x, y, color=color, marker=marker_type)
    else:
        ax.scatter(x, y, edgecolor=color, color="none", marker=marker_type)

    ax.autoscale()

    ax.set_aspect("equal")

    if title != None:
        ax.set(title=title)


def manage_plot(simulation_data, fig, ax, title, save_format='png', show=True, tight_layout=True):
    """
    Manage the plotting operations like setting titles, saving, and displaying.

    Args:
        simulation_data (list): List containing mode, beam_version, and simulation_index
        fig (matplotlib.figure.Figure): The figure object.
        ax (matplotlib.axes.Axes): The axes object for the plot.
        title (str): Title of the plot.
        save_format (str): Format in which the plot will be saved ('png', 'pdf', etc.).
        show (bool): Whether to display the plot.
        tight_layout (bool): Whether to apply tight_layout to the figure.
    """
    if title:
        ax.set_title(title)

    if tight_layout:
        plt.tight_layout()

    if save_format:
        plot_type = title.split(',')[0].lower()
        plot_filename = '{}_{}_{}_{}'.format(*simulation_data, plot_type)
        plot_path = os.path.join(BASE_DIR, 'data', 'results', plot_filename)
        fig.savefig(plot_path + save_format, dpi=600)

    if show:
        plt.show()
    else:
        plt.close(fig)
    pass


def plot_results(geometry, results):
    """
    Plot the results of the beam analysis.
    """
    plt.figure()
    for i, res in results.items():
        xi = np.cumsum([0] + geometry['L'])[i] + res['eci']
        plt.plot(xi, res['edi'], label=f'Element {i + 1}')
    plt.legend()
    plt.title('Beam Displacements')
    plt.xlabel('X Coordinate')
    plt.ylabel('Displacement')
    plt.show()

# Example usage:
# Assuming geometry, properties, loads are dictionaries prepared from generator.py
# results = solve_beam(geometry, properties, loads)
# plot_results(geometry, results)
