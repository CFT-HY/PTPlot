r"""Tests for the plots on the $(v_{\text{wall}}, \alpha_n)$ grid."""

from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
import numpy as np

from ptplot.science.plot.grid import gh21dbpl_params_figure, v_wall_alpha_n_contours
from ptplot.science.spectrum.gh21dbpl import GH21dbplParams
import ptplot.science.type_hints as th

V_WALLS: th.FloatArr1D = np.linspace(0.4, 0.9, 6)
ALPHA_NS: th.FloatArr1D = np.logspace(-2, np.log10(0.5), 5)


def test_gh21dbpl_params_figure() -> None:
    """The figure of the GH21dbpl parameters should have four panels and their colorbars."""
    fig = gh21dbpl_params_figure(GH21dbplParams.compute(v_walls=V_WALLS, alpha_ns=ALPHA_NS))
    FigureCanvasAgg(fig).draw()
    assert len(fig.axes) == 8  # noqa: PLR2004


def test_v_wall_alpha_n_contours() -> None:
    """The contour plot should have the given limits and the Chapman-Jouguet line."""
    fig = Figure()
    ax = fig.subplots()
    values = np.outer(ALPHA_NS, V_WALLS)
    v_wall_alpha_n_contours(fig, ax, V_WALLS, ALPHA_NS, values, levels=[0.01, 0.1, 0.4], label="x")
    FigureCanvasAgg(fig).draw()
    assert ax.get_xlim() == (V_WALLS[0], V_WALLS[-1])
    assert ax.get_ylim() == (ALPHA_NS[0], ALPHA_NS[-1])
    assert len(ax.get_lines()) == 1
