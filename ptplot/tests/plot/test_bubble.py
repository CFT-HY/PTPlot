"""Tests for the fluid velocity profile figure."""

from django.test import TestCase
from matplotlib.backends.backend_agg import FigureCanvasAgg
import numpy as np
from pttools.bubble import Bubble

from ptplot.science import const
from ptplot.science.plot.bubble import bubble_v_figure
from ptplot.science.spectrum.ssm import BAG


class BubbleVFigureTest(TestCase):
    """Tests for :py:func:`ptplot.science.plot.bubble.bubble_v_figure`."""

    def test_profile(self) -> None:
        """The figure should contain the velocity profile of the bubble and the title."""
        title = "Test title"
        fig = bubble_v_figure(v_wall=const.DEFAULT_V_WALL, alpha_n=const.DEFAULT_ALPHA, title=title)
        FigureCanvasAgg(fig).draw()
        ax = fig.get_axes()[0]
        bubble = Bubble(model=BAG, v_wall=const.DEFAULT_V_WALL, alpha_n=const.DEFAULT_ALPHA)
        assert any(
            np.array_equal(line.get_xdata(), bubble.xi, equal_nan=True)
            and np.array_equal(line.get_ydata(), bubble.v, equal_nan=True)
            for line in ax.get_lines()
        )
        assert ax.get_title() == title

    def test_invalid(self) -> None:
        """For parameters that have no solution, the figure should show the error instead of a profile."""
        fig = bubble_v_figure(v_wall=0.5, alpha_n=100)
        FigureCanvasAgg(fig).draw()
        ax = fig.get_axes()[0]
        assert not ax.get_lines()
        assert any("fluid shell" in text.get_text() for text in ax.texts)
