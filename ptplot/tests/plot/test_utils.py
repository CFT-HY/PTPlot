"""Tests for the plotting utilities."""

from django.test import TestCase
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.text import Text
from matplotlib.transforms import Bbox
import pytest

from ptplot.science.plot.utils import POINTS_PER_INCH, TEXT_PAD, add_text

#: Tick label formats that result in plot areas of different sizes
TICK_LABEL_FORMATS: tuple[str, ...] = ("{:.0f}", "{:.10f}", "{:.30f}")
#: Text to be added to the test figures
TEXT: str = "PTPlot test watermark"


def figure(tick_label_format: str = "{:.0f}") -> tuple[Figure, Axes]:
    """Create a figure whose plot area size depends on the width of the y tick labels."""
    fig = Figure()
    ax = fig.add_subplot()
    ax.plot([0, 1], [0, 1])
    ax.set_yticks([0, 0.5, 1], [tick_label_format.format(tick) for tick in (0, 0.5, 1)])
    return fig, ax


def text_bbox(fig: Figure, txt: Text) -> Bbox:
    """Get the bounding box of a text in figure coordinates."""
    return txt.get_window_extent().transformed(fig.transFigure.inverted())


def pad_y(fig: Figure, pad: float = TEXT_PAD) -> float:
    """Convert a padding in points to figure coordinates."""
    return pad / (fig.get_figheight() * POINTS_PER_INCH)


class AddTextTest(TestCase):
    """Tests for :func:`ptplot.science.plot.utils.add_text`.

    The tests are repeated for plot areas of different sizes,
    since the text is placed with respect to the plot area instead of the figure.
    """

    def test_within_figure(self):
        """The text should stay within the figure."""
        for tick_label_format in TICK_LABEL_FORMATS:
            with self.subTest(tick_label_format):
                fig, _ = figure(tick_label_format)
                bbox = text_bbox(fig, add_text(fig, TEXT))
                assert bbox.x0 >= 0
                assert bbox.x1 <= 1
                assert bbox.y0 >= 0
                assert bbox.y1 <= 1

    def test_does_not_overlap_plot(self):
        """The text should not overlap with the plot area."""
        for tick_label_format in TICK_LABEL_FORMATS:
            with self.subTest(tick_label_format):
                fig, ax = figure(tick_label_format)
                bbox = text_bbox(fig, add_text(ax, TEXT))
                assert bbox.y0 >= ax.get_position().y1 + pad_y(fig)

    def test_same_place_in_plot_coordinates(self):
        """The text should be placed at the same spot of the plot area, regardless of the figure layout."""
        for tick_label_format in TICK_LABEL_FORMATS:
            with self.subTest(tick_label_format):
                fig, ax = figure(tick_label_format)
                bbox = add_text(ax, TEXT).get_window_extent()
                corner_x, corner_y = ax.transAxes.transform((0, 1))
                # The text starts at the left edge of the plot area, one padding above its top edge.
                assert bbox.x0 == pytest.approx(corner_x)
                assert bbox.y0 == pytest.approx(corner_y + TEXT_PAD * fig.dpi / POINTS_PER_INCH)

    def test_figure_and_axes_equivalent(self):
        """Giving a figure should place the text the same way as giving its first axes."""
        fig_from_figure, _ = figure()
        fig_from_axes, ax_from_axes = figure()
        bbox_from_figure = text_bbox(fig_from_figure, add_text(fig_from_figure, TEXT))
        bbox_from_axes = text_bbox(fig_from_axes, add_text(ax_from_axes, TEXT))
        assert bbox_from_figure.bounds == pytest.approx(bbox_from_axes.bounds)

    def test_no_axes(self):
        """Adding text to a figure without axes should fail with a clear error."""
        with pytest.raises(ValueError, match="no axes"):
            add_text(Figure(), TEXT)
