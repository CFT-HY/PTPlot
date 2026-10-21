"""Tests for the bubble profile figures."""

import typing as tp

from django.test import TestCase
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
import numpy as np
from pttools.bubble import Bubble

from ptplot.science import const
from ptplot.science.plot.bubble import bubble_v_figure, bubble_w_figure
from ptplot.science.spectrum.ssm import BAG

#: Figure functions and the profiles that they should plot
FIGURES: tuple[tuple[tp.Callable[..., Figure], tp.Callable[[Bubble], np.ndarray]], ...] = (
    (bubble_v_figure, lambda bubble: bubble.v),
    (bubble_w_figure, lambda bubble: bubble.w / bubble.wn),
)


class BubbleFigureTest(TestCase):
    """Tests for the figures of :py:mod:`ptplot.science.plot.bubble`."""

    def test_profile(self) -> None:
        """The figures should contain the profiles of the bubble and the title."""
        title = "Test title"
        bubble = Bubble.cached(model=BAG, v_wall=const.DEFAULT_V_WALL, alpha_n=const.DEFAULT_ALPHA)
        for figure, profile in FIGURES:
            with self.subTest(figure=figure.__name__):
                fig = figure(v_wall=const.DEFAULT_V_WALL, alpha_n=const.DEFAULT_ALPHA, title=title)
                FigureCanvasAgg(fig).draw()
                ax = fig.get_axes()[0]
                assert any(
                    np.array_equal(line.get_xdata(), bubble.xi, equal_nan=True)
                    and np.allclose(line.get_ydata(), profile(bubble), equal_nan=True)
                    for line in ax.get_lines()
                )
                assert ax.get_title() == title

    def test_w_outside(self) -> None:
        r"""The normalised enthalpy should be 1 outside the bubble, where $w = w_n$."""
        bubble = Bubble.cached(model=BAG, v_wall=const.DEFAULT_V_WALL, alpha_n=const.DEFAULT_ALPHA)
        fig = bubble_w_figure(v_wall=const.DEFAULT_V_WALL, alpha_n=const.DEFAULT_ALPHA)
        line = fig.get_axes()[0].get_lines()[0]
        xi = np.asarray(line.get_xdata())
        w = np.asarray(line.get_ydata())
        assert w[-1] == 1
        assert np.allclose(w[xi > bubble.v_sh], 1)

    def test_invalid(self) -> None:
        """For parameters that have no solution, the figures should show the error instead of a profile."""
        for figure, _ in FIGURES:
            with self.subTest(figure=figure.__name__):
                fig = figure(v_wall=0.5, alpha_n=100)
                FigureCanvasAgg(fig).draw()
                ax = fig.get_axes()[0]
                assert not ax.get_lines()
                assert any("fluid shell" in text.get_text() for text in ax.texts)
