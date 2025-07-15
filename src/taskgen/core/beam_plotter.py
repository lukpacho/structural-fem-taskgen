# beam_plotter.py
import os

import matplotlib.pyplot as plt
import numpy as np
from adjustText import adjust_text

# from calfem.vis_mpl import *
from calfem.vis_mpl import pltstyle2, scalfact2

from .config import CM_TO_IN, M_TO_CM, results_dir

# from matplotlib.backends.backend_pdf import PdfPages


def plot_beam_results(ex, ey, element_results, max_results, mode, beam_version, simulation_index=0):
    plt.rcParams.update({"font.size": 9})
    simulation_data = [mode, beam_version, simulation_index]
    plot_filename = "{}_{}_{}.pdf".format(*simulation_data)
    plot_path = os.path.join(results_dir(), plot_filename)
    plot_functions = [
        plot_beam_displacements,
        plot_beam_shear_forces,
        plot_beam_moments,
    ]
    plot_titles = ["Displacement, cm", "Shear Force, kN", "Moment, kNm"]
    max_result_keys = ["displacement", "shear_force", "moment"]

    # Create a figure with three subplots
    fig, axes = plt.subplots(nrows=3, ncols=1, figsize=(16 * CM_TO_IN, 25 * CM_TO_IN))
    for ax, plot_function, title, key in zip(axes, plot_functions, plot_titles, max_result_keys):
        plot_function(ax, ex, ey, element_results, max_results[key])
        ax.axis("off")
        ax.set_title(title)

    plt.tight_layout()

    fig.savefig(plot_path, format="pdf")
    plt.close(fig)


def plot_beam_displacements(ax, ex, ey, element_results, max_result):
    scale_factor = scalfact2(ex, ey, max_result, 0.3)
    texts = []
    annotated_positions = set()
    for i, result in element_results.items():
        edi = result["edi"]
        dispbeam2_ax(ax, ex[i], ey[i], edi, [1, 2, 3], scale_factor)
        annotate_values(
            ax,
            ex[i],
            ey[i],
            edi[:, 1],
            scale_factor,
            texts,
            annotated_positions,
            value_conversion=lambda v: v * M_TO_CM,
        )
    add_annotations(ax, texts)


def plot_beam_shear_forces(ax, ex, ey, element_results, max_result):
    scale_factor = scalfact2(ex, ey, max_result, 0.3)
    texts = []
    annotated_positions = set()
    for i, result in element_results.items():
        shear_force = result["es"][:, 1]
        secforce2_ax_fill(ax, ex[i], ey[i], shear_force, [2, 1], scale_factor)
        annotate_values(ax, ex[i], ey[i], -shear_force, scale_factor, texts, annotated_positions)
    add_annotations(ax, texts)


def plot_beam_moments(ax, ex, ey, element_results, max_result):
    scale_factor = scalfact2(ex, ey, max_result, 0.3)
    texts = []
    annotated_positions = set()
    for i, result in element_results.items():
        moments = result["es"][:, 2]
        secforce2_ax_fill(ax, ex[i], ey[i], moments, [2, 1], scale_factor)
        annotate_values(ax, ex[i], ey[i], -moments, scale_factor, texts, annotated_positions)
    add_annotations(ax, texts)


def annotate_values(
    ax, ex, ey, data, scale_factor, texts, annotated_positions, value_conversion=None
):
    n_points = len(data)
    x_positions = np.linspace(ex[0], ex[1], n_points)
    y_positions = np.linspace(ey[0], ey[1], n_points)
    max_idx = np.argmax(data)
    min_idx = np.argmin(data)
    indices = [
        0,
        len(data) // 2,
        -1,
        max_idx,
        min_idx,
    ]  # Indices for start, mid, end, max, and min positions

    for idx in indices:
        position_x = x_positions[idx]
        position_y = y_positions[idx] + data[idx] * scale_factor
        value = data[idx]

        if value_conversion:
            value = value_conversion(value)

        pos_key = (round(position_x, 5), round(position_y, 5))

        if pos_key in annotated_positions:
            continue

        annotated_positions.add(pos_key)

        dx = ex[1] - ex[0]
        dy = ey[1] - ey[0]
        offset_magnitude = 0.2 * np.hypot(dx, dy)

        offset_x, offset_y = calculate_offset(dx, dy, value, offset_magnitude)

        text = ax.text(
            position_x + offset_x,
            position_y + offset_y,
            f"{np.abs(value):.2f}",
            ha="center",
            va="center",
            bbox=dict(boxstyle="round4,pad=0.2", fc="white", ec="gray", alpha=0.8),
        )
        texts.append((text, position_x, position_y))


def calculate_offset(dx, dy, value, offset_magnitude):
    # Compute unit vectors
    length = np.hypot(dx, dy) if np.hypot(dx, dy) != 0 else 1e-6
    unit_tangent_x = dx / length
    unit_tangent_y = dy / length
    unit_perp_x = -unit_tangent_y
    unit_perp_y = unit_tangent_x

    # Determine horizontal offset based on beam's slope
    if dy > 0:
        offset_x = -offset_magnitude * abs(unit_perp_x)  # Push left
    elif dy < 0:
        offset_x = offset_magnitude * abs(unit_perp_x)  # Push right
    else:
        offset_x = 0  # No horizontal offset

    # Determine vertical offset based on value position
    if value >= 0:
        offset_y = offset_magnitude * abs(unit_perp_y)  # Push up
    else:
        offset_y = -offset_magnitude * abs(unit_perp_y)  # Push down

    return offset_x, offset_y


def add_annotations(ax, texts):
    text_objects = [text for text, _, _ in texts]
    adjust_text(
        text_objects,
        ax=ax,
        expand_text=(1.25, 1.25),
        force_text=(0.5, 0.5),
        force_points=(0.2, 0.5),
        min_arrow_len=0.001,
        lim=1000,
    )

    for text, position_x, position_y in texts:
        text_pos = text.get_position()
        ax.annotate(
            "",
            xy=(position_x, position_y),
            xytext=text_pos,
            arrowprops=dict(arrowstyle="->", color="gray", lw=1.1, shrinkA=4, shrinkB=0, alpha=0.6),
        )


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

    # Plot element
    ax.plot(ex, ey, color="black", linewidth=1)

    A1 = np.array([A[0, 0], A[Nbr - 1, 0]]).reshape(1, 2)
    A2 = np.array([A[0, 1], A[Nbr - 1, 1]]).reshape(1, 2)
    draw_node_circles_ax(ax, A1, A2, color=node_color, filled=False, marker_type=node_style)


def draw_node_circles_ax(
    ax,
    ex,
    ey,
    title="",
    color=(0, 0, 0),
    face_color=(0.8, 0.8, 0.8),
    filled=False,
    marker_type="o",
):
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

    # nel = ex.shape[0]
    # nnodes = ex.shape[1]
    #
    # nodes = []

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

    if title is not None:
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
