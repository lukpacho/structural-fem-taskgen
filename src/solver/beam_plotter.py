from calfem.vis_mpl import *
from config import BASE_DIR, ANNOTATION_DISPLACEMENT_MINIMUM, ANNOTATION_THRESHOLD, cm, m_to_cm


def plot_beam_results(ex, ey, element_results, max_results, mode, beam_version, simulation_index=0):
    plt.rcParams.update({'font.size': 9})
    simulation_data = [mode, beam_version, simulation_index]

    # Plot displacements
    fig, ax = plt.subplots(figsize=(16 * cm, 8 * cm))
    plot_beam_displacements(ax, ex, ey, element_results, max_results['displacement'])
    manage_plot(simulation_data, fig, ax, 'Displacements, cm')

    # Plot shear forces
    fig, ax = plt.subplots(figsize=(16 * cm, 8 * cm))
    plot_beam_shear_forces(ax, ex, ey, element_results, max_results['shear_force'])
    manage_plot(simulation_data, fig, ax, 'Shear Forces, kN')

    # Plot moments
    fig, ax = plt.subplots(figsize=(16 * cm, 8 * cm))
    plot_beam_moments(ax, ex, ey, element_results, max_results['moment'])
    manage_plot(simulation_data, fig, ax, 'Moments, kNm')


def plot_beam_displacements(ax, ex, ey, element_results, max_result):
    scale_factor = scalfact2(ex, ey, max_result, 0.3)
    eldraw2(ex, ey, [2, 1, 0])  # Line type, line color, node mark

    annotation_positions = []
    for i, result in element_results.items():
        edi = result['edi']
        dispbeam2_ax(ax, ex[i], ey[i], edi, [1, 2, 3], scale_factor)
        annotate_displacements(ax, ex[i], ey[i], edi, scale_factor, annotation_positions)


def plot_beam_shear_forces(ax, ex, ey, element_results, max_result):
    scale_factor = scalfact2(ex, ey, max_result, 0.3)

    annotation_positions = []
    for i, result in element_results.items():
        shear_force = result['es'][:, 1]
        secforce2_ax_fill(ax, ex[i], ey[i], shear_force, [2, 1],  scale_factor)
        annotate_internal_forces(ax, ex[i], ey[i], -shear_force, scale_factor, annotation_positions)


def plot_beam_moments(ax, ex, ey, element_results, max_result):
    scale_factor = scalfact2(ex, ey, max_result, 0.3)

    annotation_positions = []
    for i, result in element_results.items():
        moments = result['es'][:, 2]
        secforce2_ax_fill(ax, ex[i], ey[i], moments, [2, 1],  scale_factor)
        annotate_internal_forces(ax, ex[i], ey[i], -moments, scale_factor, annotation_positions)


def annotate_displacements(ax, ex, ey, edi, scale_factor, annotation_positions):
    # Ensure ex and ey have correct sizes reflecting the size of edi
    n_points = len(edi)
    x_positions = np.linspace(ex[0], ex[1], n_points)
    y_positions = np.linspace(ey[0], ey[1], n_points)

    # Indices for start, mid, end, max, and min positions
    max_idx = np.argmax(edi[:, 1])
    min_idx = np.argmin(edi[:, 1])
    indices = [0, len(edi) // 2, -1, max_idx, min_idx]
    positions = [(x_positions[idx], y_positions[idx] + edi[idx, 1] * scale_factor) for idx in indices]
    displacement_values = [edi[idx, 1] * m_to_cm for idx in indices]  # Convert displacement to cm

    for (pos_x, pos_y), displacement_value in zip(positions, displacement_values):
        if not is_near_other_annotations(pos_x, pos_y, annotation_positions):
            annotation = adjust_annotation_position(ax, pos_x, pos_y, f'{displacement_value:.2f}', annotation_positions)
            annotation_positions.append((pos_x, pos_y))


def annotate_internal_forces(ax, ex, ey, force, scale_factor, annotation_positions):
    # Ensure ex and ey have correct sizes reflecting the size of force
    n_points = len(force)
    x_positions = np.linspace(ex[0], ex[1], n_points)
    y_positions = np.linspace(ey[0], ey[1], n_points)

    # Max and min force annotations
    max_idx = np.argmax(force)
    min_idx = np.argmin(force)

    # Annotation indices for start, mid, and end positions
    indices = [0, len(force) // 2, -1, max_idx, min_idx]
    positions = [(x_positions[idx], y_positions[idx] + force[idx] * scale_factor) for idx in indices]
    values = [force[idx] for idx in indices]

    for (pos_x, pos_y), val in zip(positions, values):
        if not is_near_other_annotations(pos_x, pos_y, annotation_positions):
            annotation = adjust_annotation_position(ax, pos_x, pos_y, f'{val:.2f}', annotation_positions)
            annotation_positions.append((pos_x, pos_y))


def is_near_plot_edge(pos_x, pos_y, ax, offset=0.1):
    """ Check if the annotation is near the plot edge """
    xlim = ax.get_xlim()
    ylim = ax.get_ylim()
    return not (xlim[0] + offset < pos_x < xlim[1] - offset and ylim[0] + offset < pos_y < ylim[1] - offset)


def is_near_other_annotations(pos_x, pos_y, positions, threshold=ANNOTATION_THRESHOLD):
    return any(np.sqrt((x - pos_x) ** 2 + (y - pos_y) ** 2) < threshold for x, y in positions)


def adjust_annotation_position(ax, pos_x, pos_y, text, annotation_positions):
    """Adjust the annotation position if it overlaps with the plot edge or other annotations"""
    predefined_offsets = [(0, 10), (10, 10), (-10, 10), (0, -10), (10, -10), (-10, -10),
                          (0, 20), (20, 20), (-20, 20), (0, -20), (20, -20), (-20, -20)]
    for offset in predefined_offsets:
        annotation = ax.annotate(text, xy=(pos_x, pos_y), textcoords="offset points", xytext=offset,
                                 ha='center', va='bottom', arrowprops=dict(arrowstyle="->", connectionstyle="arc3", color='blue'),
                                 bbox=dict(boxstyle="round,pad=0.5", facecolor='yellow', edgecolor='black', alpha=0.5))
        ax.figure.canvas.draw()
        bbox = annotation.get_window_extent(renderer=ax.figure.canvas.get_renderer())

        # Check if the annotation is near the plot edge or other annotations
        if not is_near_plot_edge(pos_x + offset[0], pos_y + offset[1], ax):
            if not is_near_other_annotations(bbox.x0, bbox.y0, annotation_positions):
                annotation_positions.append((pos_x + offset[0], pos_y + offset[1]))
                return annotation

        # Remove the annotation if it doesn't fit
        annotation.remove()

    # If no suitable position found, return the original position
    return ax.annotate(text, xy=(pos_x, pos_y), textcoords="offset points", xytext=(0, 10), ha='center', va='bottom',
                       arrowprops=dict(arrowstyle="->", connectionstyle="arc3", color='blue'),
                       bbox=dict(boxstyle="round,pad=0.5", facecolor='yellow', edgecolor='black', alpha=0.5))


def manage_plot(simulation_data, fig, ax, title, axis=False, save_format='png', show=True, tight_layout=True):
    """
    Manage the plotting operations like setting titles, saving, and displaying.

    Args:
        simulation_data (list): List containing mode, beam_version, and simulation_index
        fig (matplotlib.figure.Figure): The figure object.
        ax (matplotlib.axes.Axes): The axes object for the plot.
        title (str): Title of the plot.
        axis (bool): Whether the plot should be drawn on the axis or not.
        save_format (str): Format in which the plot will be saved ('png', 'pdf', etc.).
        show (bool): Whether to display the plot.
        tight_layout (bool): Whether to apply tight_layout to the figure.
    """
    if not axis:
        ax.axis('off')

    if title:
        ax.set_title(title)

    if tight_layout:
        plt.tight_layout()

    if save_format:
        plot_type = title.split(',')[0].lower()
        plot_filename = '{}_{}_{}_{}'.format(*simulation_data, plot_type)
        plot_path = os.path.join(BASE_DIR, 'data', 'results', plot_filename)
        fig.savefig(f'{plot_path}.{save_format}', dpi=600)

    if show:
        plt.show()
    else:
        plt.close(fig)


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


def secforce2_ax_fill(ax, ex, ey, es, plotpar=[2, 1], sfac=None, eci=None):
    """
    secforce2(ex,ey,es,plotpar,sfac)
    secforce2(ex,ey,es,plotpar,sfac,eci)
    [sfac]=secforce2(ex,ey,es)
    [sfac]=secforce2(ex,ey,es,plotpar)
    --------------------------------------------------------------------------
    PURPOSE:
    Draw section force diagram for a two dimensional bar or beam element.

    INPUT:  ex = [ x1 x2 ]
                ey = [ y1 y2 ]	element node coordinates.

                es = [ S1;
                   S2;
                        ... ] 	vector containing the section force
                                        in Nbr evaluation points along the element.

            plotpar=[linecolour, elementcolour]

                linecolour=1 -> black      elementcolour=1 -> black
                           2 -> blue                     2 -> blue
                           3 -> magenta                  3 -> magenta
                           4 -> red                       4 -> red

                sfac = [scalar]	scale factor for section force diagrams.

            eci = [  x1;
                     x2;
                   ... ]  local x-coordinates of the evaluation points (Nbr).
                          If not given, the evaluation points are assumed to be uniformly
                          distributed
    --------------------------------------------------------------------------

    LAST MODIFIED: O Dahlblom  2019-12-16
                   O Dahlblom  2023-01-31 (Python)

    Copyright (c)  Division of Structural Mechanics and
                   Division of Solid Mechanics.
                   Lund University
    --------------------------------------------------------------------------
    """
    if ex.shape != ey.shape:
        raise ValueError("Check size of ex, ey dimensions.")

    c = len(es)
    Nbr = c

    x1, x2 = ex
    y1, y2 = ey
    dx = x2 - x1
    dy = y2 - y1
    L = np.sqrt(dx * dx + dy * dy)
    nxX = dx / L
    nyX = dy / L
    n = np.array([nxX, nyX])

    if sfac is None:
        sfac = (0.2 * L) / max(abs(es))

    if eci is None:
        eci = np.arange(0.0, L + L / (Nbr - 1), L / (Nbr - 1)).reshape(Nbr, 1)

    p1 = plotpar[0]
    line_color = get_color(p1)

    p2 = plotpar[1]
    element_color = get_color(p2)

    a = len(eci)
    if a != c:
        raise ValueError("Check size of eci dimension.")

    es = es * sfac

    # From local x-coordinates to global coordinates of the element
    A = np.zeros(2 * Nbr).reshape(Nbr, 2)
    A[0, 0] = ex[0]
    A[0, 1] = ey[0]
    for i in range(Nbr):
        A[i, 0] = A[0, 0] + eci[i] * n[0]
        A[i, 1] = A[0, 1] + eci[i] * n[1]

    B = np.array(A)

    # Plot diagram
    for i in range(0, Nbr):
        A[i, 0] = A[i, 0] + es[i] * n[1]
        A[i, 1] = A[i, 1] - es[i] * n[0]

    xc = np.array(A[:, 0])
    yc = np.array(A[:, 1])

    # Create a closed shape for fill
    xc_closed = np.concatenate([xc, ex[::-1]])
    yc_closed = np.concatenate([yc, ey[::-1]])

    ax.fill(xc_closed, yc_closed, color=line_color, alpha=0.2)
    ax.plot(xc, yc, color=line_color, linewidth=1)

    # Plot stripes in diagram
    for i in range(Nbr):
        xs = [B[i, 0], A[i, 0]]
        ys = [B[i, 1], A[i, 1]]
        ax.plot(xs, ys, color=line_color, linewidth=1, alpha=0.3)

    # Plot element
    ax.plot(ex, ey, color=element_color, linewidth=2)


def get_color(index):
    if index == 1:
        return 0, 0, 0
    elif index == 2:
        return 0, 0, 1
    elif index == 3:
        return 1, 0, 1
    elif index == 4:
        return 1, 0, 0
    else:
        raise ValueError("Invalid color index.")
