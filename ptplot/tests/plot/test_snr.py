"""Tests for the SNR figures."""

import base64
import functools
import json

from django.test import TestCase
from matplotlib.figure import Figure
import numpy as np
import plotly.graph_objects as go
import pytest

from ptplot.science import const
from ptplot.science.plot.logarithmic import flat_points
from ptplot.science.plot.snr import (
    PARAM_LABELS_HTML,
    PLOTLY_N_F,
    PLOTLY_SCRIPT,
    SNRFigure,
    decade_label,
    snr_figure_grid,
)
from ptplot.science.plot.snr_alpha_beta import SNRFigureAlphaBeta
from ptplot.science.plot.snr_ubarf_rstar import SNRFigureUbarfRStar
from ptplot.science.snr.grid import GridAxes
from ptplot.science.snr.grid_alpha_beta import SNRGridAlphaBeta
from ptplot.science.snr.grid_ubarf_rstar import SNRGridUbarfRStar
from ptplot.science.type_hints import FloatArr1D
from ptplot.science.utils import atleast_2d
from ptplot.tests.const import TEST_GRID_SIZE

#: Points of the test grids [scenario, point]
ALPHA_POINTS: list[FloatArr1D] = [np.array([0.1, 0.2]), np.array([0.5])]
BETA_TILDE_POINTS: list[FloatArr1D] = [np.array([100., 50.]), np.array([20.])]
LABELS: list[list[str]] = [["A", "B"], ["C"]]
TITLES: list[str] = ["Scenario 1", "Scenario 2"]
#: Highlighted points by their indices in the flattened points, i.e. "B" and "C"
HIGHLIGHTS: dict[str, int] = {"Highlight 1": 1, "Highlight 2": 2}


@functools.cache
def grids() -> tuple[SNRGridAlphaBeta, SNRGridUbarfRStar]:
    """Small SNR grids with two scenarios of points."""
    kwargs = {
        "T_star": const.DEFAULT_T_STAR, "g_star": const.DEFAULT_G_STAR, "v_wall": const.DEFAULT_V_WALL,
        "alpha_points": ALPHA_POINTS, "beta_tilde_points": BETA_TILDE_POINTS,
        "v_wall_points": [np.full_like(points, const.DEFAULT_V_WALL) for points in ALPHA_POINTS],
        "labels_points": LABELS, "titles": TITLES, "axes": GridAxes(size=TEST_GRID_SIZE),
        "log_progress_percentage": None,
    }
    return SNRGridAlphaBeta(**kwargs), SNRGridUbarfRStar(**kwargs)


def figures() -> list[SNRFigure]:
    """SNR figures of the test grids, both with and without filling."""
    grid_ab, grid_ur = grids()
    return [
        figure
        for filled in (False, True)
        for figure in (SNRFigureAlphaBeta(grid_ab, filled=filled), SNRFigureUbarfRStar(grid_ur, filled=filled))
    ]


def highlighted_figures(filled: bool = False) -> list[SNRFigure]:
    """SNR figures of the test grids with the points of :py:data:`HIGHLIGHTS` highlighted."""
    grid_ab, grid_ur = grids()
    return [
        SNRFigureAlphaBeta(grid_ab, filled=filled, highlights=HIGHLIGHTS),
        SNRFigureUbarfRStar(grid_ur, filled=filled, highlights=HIGHLIGHTS),
    ]


def trace_by_uid(fig: go.Figure, uid: str) -> go.Scatter:
    """Get the trace of a Plotly figure by its uid."""
    return next(fig.select_traces(selector={"uid": uid}))


class SNRFigureTest(TestCase):
    """Tests for the SNR figures."""

    @staticmethod
    def test_matplotlib() -> None:
        """The Matplotlib figures should be created."""
        for figure in figures():
            assert isinstance(figure.matplotlib(), Figure)

    @staticmethod
    def test_f_indices() -> None:
        """The spectra should be subsampled to at most the given number of frequencies, including both ends."""
        figure = figures()[0]
        n_f_grid = figure.grid.f.size
        for n_f in (10, PLOTLY_N_F, n_f_grid, 2 * n_f_grid):
            indices = figure.f_indices(n_f)
            assert indices.size == min(n_f, n_f_grid)
            assert indices[0] == 0
            assert indices[-1] == n_f_grid - 1
            assert np.all(np.diff(indices) > 0)

    @staticmethod
    def test_plotly() -> None:
        """The Plotly figure should show the points and the spectrum of the grid point nearest to the first point."""
        for figure in figures():
            fig = figure.plotly()
            grid = figure.grid
            point_traces = [trace for trace in fig.select_traces() if trace.name in TITLES]
            assert [trace.name for trace in point_traces] == TITLES
            assert [list(trace.text) for trace in point_traces] == LABELS

            iy, ix = figure.initial_indices()
            x_points, y_points = atleast_2d(*grid.points())
            assert ix == np.abs(np.log10(grid.x) - np.log10(x_points[0][0])).argmin()
            assert iy == np.abs(np.log10(grid.y) - np.log10(y_points[0][0])).argmin()
            selected = trace_by_uid(fig, "selected")
            assert selected.x[0] == figure.x_log10[ix]
            assert selected.y[0] == figure.y_log10[iy]
            spectrum = trace_by_uid(fig, "spectrum")
            f_indices = figure.f_indices()
            np.testing.assert_array_equal(spectrum.x, grid.f[f_indices])
            np.testing.assert_array_equal(spectrum.y, grid.spectra[iy, ix, f_indices])
            info = next(fig.select_annotations(selector={"name": "selected"}))
            for name in ("alpha", "beta_tilde", "ubarf", "r_star"):
                assert f"{PARAM_LABELS_HTML[name]} = {grid.spectrum_params[name][iy, ix]:.3g}" in info.text
            assert f"SNR = {grid.snr[iy, ix]:.3g}" in info.text

    @staticmethod
    def test_plotly_data() -> None:
        """The embedded spectra should be the subsampled spectra of the grid as 32-bit floats in the [y, x, f] order."""
        for figure in figures():
            grid = figure.grid
            n_f = 50
            data = json.loads(json.dumps(figure.plotly_data(n_f)))
            f_indices = figure.f_indices(n_f)
            spectra = np.frombuffer(base64.b64decode(data["spectra"]), dtype="<f4")
            np.testing.assert_array_equal(
                spectra.reshape(grid.y.size, grid.x.size, f_indices.size),
                grid.spectra[:, :, f_indices].astype(np.float32)
            )
            np.testing.assert_array_equal(data["f"], grid.f[f_indices])
            np.testing.assert_array_equal(data["x"], grid.x)
            np.testing.assert_array_equal(data["y"], grid.y)
            np.testing.assert_array_equal(np.array(data["snr"], dtype=np.float64), grid.snr)
            assert [param["label"] for param in data["params"]] == [
                PARAM_LABELS_HTML[name] for name in grid.spectrum_params
            ]
            for param, values in zip(data["params"], grid.spectrum_params.values(), strict=True):
                np.testing.assert_array_equal(np.array(param["values"], dtype=np.float64), values)

    @staticmethod
    def test_plotly_html() -> None:
        """The HTML should contain the figure, the data of the grid and the script that handles the clicks."""
        for figure in figures():
            html = figure.plotly_html(full_html=False, include_plotlyjs=False)
            assert "plotly_click" in html
            assert PLOTLY_SCRIPT.rsplit("__DATA__", 1)[1] in html
            assert figure.plotly_data()["spectra"] in html
            assert "__DATA__" not in html
            assert "{plot_id}" not in html


class SNRFigureHighlightTest(TestCase):
    """Tests for the highlighted points and the subplots of the SNR figures."""

    @staticmethod
    def test_flat_points() -> None:
        """The points of the scenarios should follow each other."""
        x, y = flat_points(ALPHA_POINTS, BETA_TILDE_POINTS)
        np.testing.assert_array_equal(x, [0.1, 0.2, 0.5])
        np.testing.assert_array_equal(y, [100., 50., 20.])
        x, y = flat_points(0.1, 100.)
        np.testing.assert_array_equal(x, [0.1])
        np.testing.assert_array_equal(y, [100.])

    @staticmethod
    def test_matplotlib() -> None:
        """The highlighted points should be drawn at the right places and added to the legend of the scenarios."""
        for filled in (False, True):
            for figure in highlighted_figures(filled=filled):
                grid = figure.grid
                ax = figure.matplotlib().get_axes()[0]
                legend = ax.get_legend()
                assert legend is not None
                assert [text.get_text() for text in legend.get_texts()] == TITLES + list(HIGHLIGHTS)
                x_flat, y_flat = flat_points(*grid.points())
                highlighted = ax.get_lines()[-len(HIGHLIGHTS):]
                for line, index in zip(highlighted, HIGHLIGHTS.values(), strict=True):
                    np.testing.assert_allclose(np.asarray(line.get_xdata(), dtype=np.float64), np.log10(x_flat[index]))
                    np.testing.assert_allclose(np.asarray(line.get_ydata(), dtype=np.float64), np.log10(y_flat[index]))

    @staticmethod
    def test_plotly() -> None:
        """The highlighted points should be drawn at the right places with their labels."""
        for figure in highlighted_figures():
            grid = figure.grid
            fig = figure.plotly()
            x_flat, y_flat = flat_points(*grid.points())
            for label, index in HIGHLIGHTS.items():
                trace = next(fig.select_traces(selector={"name": label}))
                np.testing.assert_allclose(trace.x, [np.log10(x_flat[index])])
                np.testing.assert_allclose(trace.y, [np.log10(y_flat[index])])

    @staticmethod
    def test_no_highlights() -> None:
        """Without highlights, the legend should contain only the scenarios."""
        fig = SNRFigureAlphaBeta(grids()[0]).matplotlib()
        legend = fig.get_axes()[0].get_legend()
        assert legend is not None
        assert [text.get_text() for text in legend.get_texts()] == TITLES

    @staticmethod
    def test_highlights_without_points() -> None:
        """Points cannot be highlighted on a grid without points."""
        grid = SNRGridAlphaBeta(
            T_star=const.DEFAULT_T_STAR, g_star=const.DEFAULT_G_STAR, v_wall=const.DEFAULT_V_WALL,
            alpha_n=np.array([0.1, 1.]), beta_tilde=np.array([100., 1000.])
        )
        with pytest.raises(ValueError, match="no points"):
            SNRFigureAlphaBeta(grid, highlights=HIGHLIGHTS)

    @staticmethod
    def test_figure_grid() -> None:
        """Each figure should be drawn as a subplot with its title, and the unused subplots should be removed."""
        figs = figures()[:3]
        titles = ["A", "B", "C"]
        fig = snr_figure_grid(figs, titles=titles)
        plot_axes = [ax for ax in fig.get_axes() if ax.get_title()]
        assert [ax.get_title() for ax in plot_axes] == titles
        # The third subplot is at the start of the second row.
        assert plot_axes[2].get_position().x0 == pytest.approx(plot_axes[0].get_position().x0)
        assert plot_axes[2].get_position().y1 < plot_axes[0].get_position().y0
        # The watermark is above the first subplot, and the titles above it.
        watermarks = [[text for text in ax.texts if text.get_text().startswith("PTPlot")] for ax in plot_axes]
        assert [len(texts) for texts in watermarks] == [1, 0, 0]
        assert plot_axes[0].title.get_window_extent().y0 >= watermarks[0][0].get_window_extent().y1
        fig_default = snr_figure_grid(figs)
        assert [ax.get_title() for ax in fig_default.get_axes() if ax.get_title()] == [
            figure.grid.name for figure in figs
        ]


def test_decade_label() -> None:
    """The tick labels should be powers of ten, except 1 for 10^0, as on the logarithmic axes of Plotly."""
    assert decade_label(-2) == "10<sup>-2</sup>"
    assert decade_label(0) == "1"
    assert decade_label(-0.) == "1"
    assert decade_label(3) == "10<sup>3</sup>"
