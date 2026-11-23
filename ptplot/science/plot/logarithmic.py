"""Figures with logarithmic axes."""

import typing as tp

from matplotlib.axes import Axes
from matplotlib.figure import Figure
import numpy as np

from ptplot.science import const
from ptplot.science.plot.ticks import add_ticks
import ptplot.science.type_hints as th
from ptplot.science.utils import atleast_2d

__all__ = [
    "HIGHLIGHT_MARKERS",
    "HIGHLIGHT_ZORDER",
    "POINTS_ZORDER",
    "add_highlights",
    "add_points",
    "log_figure",
    "nested_labels",
]

#: Markers of the highlighted points, see :py:func:`add_highlights`.
#: These have the same shape and therefore the same visual size.
HIGHLIGHT_MARKERS: tuple[str, ...] = ("^", "v", "<", ">")
#: Z-order of the highlighted points, see :py:func:`add_highlights`.
#: This is above the contours, but below the points, so that the highlighted points remain visible.
HIGHLIGHT_ZORDER: float = 2.5
#: Z-order of the points, see :py:func:`add_points`.
#: This is above the highlighted points, but below the legend.
POINTS_ZORDER: float = 3


def add_points(
        ax: Axes,
        x: th.FloatOrArrOrList1D2D,
        y: th.FloatOrArrOrList1D2D,
        labels: th.StrOrListOrNestedList | None = None,
        titles: th.StrOrList | None = None) -> tuple[th.ArrOrListOfArrs, th.ArrOrListOfArrs]:
    r"""Add points to a $(\alpha, \beta/H)$ plot.

    The points are drawn above the highlighted points of :py:func:`add_highlights`, see :py:data:`POINTS_ZORDER`.
    """
    x2, y2 = atleast_2d(x, y)
    labels = nested_labels(labels)

    # Iterate over scenarios
    for i, (x_set, y_set) in enumerate(zip(x2, y2, strict=True)):
        x_log_set = np.log10(x_set)
        y_log_set = np.log10(y_set)

        # Plot points
        ax.plot(x_log_set, y_log_set, ".", zorder=POINTS_ZORDER)
        # Add labels to points
        if labels:
            label_set = labels[i]
            for xi, yi, label in zip(x_log_set, y_log_set, label_set, strict=True):
                ax.annotate(label, xy=(xi, yi), xycoords="data", xytext=(5, 0), textcoords="offset points")

    if titles:
        ax.legend(
            [titles] if isinstance(titles, str) else titles,
            loc="lower left", framealpha=0.9
        )

    return x2, y2


def add_highlights(
        ax: Axes,
        highlights: dict[str, tuple[float, float]]) -> None:
    r"""Highlight some points of a plot with logarithmic values on linear axes, e.g. an SNR figure.

    Each highlighted point is drawn with a marker of its own, which is added to the legend with its label.
    The markers are drawn below the points of :py:func:`add_points`, see :py:data:`HIGHLIGHT_ZORDER`,
    so that the points remain visible within the markers.
    The existing entries of the legend, e.g. those of :py:func:`add_points`, are kept.

    :param ax: Axes to draw on
    :param highlights: Labels of the highlighted points, and their x and y values,
        e.g. from :py:meth:`ptplot.science.snr.grid.SNRGrid.point_coords`
    """
    legend = ax.get_legend()
    handles: list[tp.Any] = [] if legend is None else list(legend.legend_handles)
    labels: list[str] = [] if legend is None else [text.get_text() for text in legend.get_texts()]
    for i, (label, (x, y)) in enumerate(highlights.items()):
        handles += ax.plot(
            np.log10(x), np.log10(y),
            marker=HIGHLIGHT_MARKERS[i % len(HIGHLIGHT_MARKERS)], markersize=10,
            color="red", markeredgecolor="black", linestyle="none", zorder=HIGHLIGHT_ZORDER
        )
        labels.append(label)
    ax.legend(handles, labels, loc="lower left", framealpha=0.9)


def nested_labels(labels: th.StrOrListOrNestedList | None) -> list[list[str]] | None:
    """Convert the labels of the points to the form [scenario, point].

    :param labels: A label of a single point, labels of the points of a single scenario, or labels [scenario, point]
    :return: Labels [scenario, point], or None if there are no labels
    """
    if not labels:
        return None
    if isinstance(labels, str):
        return [[labels]]
    if isinstance(labels[0], str):
        return [tp.cast("list[str]", labels)]
    return tp.cast("list[list[str]]", labels)


def log_figure(
        x: th.FloatArr1D,
        y: th.FloatArr1D,
        xlabel: str,
        ylabel: str,
        fig: Figure | None = None,
        ax: Axes | None = None,
        xtickpos: th.IntArr1D | None = None,
        ytickpos: th.IntArr1D | None = None,
        xticklabels: list[str] | None = None,
        yticklabels: list[str] | None = None,
        label_fontsize: int = const.DEFAULT_LABEL_FONTSIZE) -> tuple[Figure, Axes, tuple[float, float, float, float]]:
    """Create a figure that has logarithmic tick labels on linear axes.

    :param fig: Figure of the axes. If the axes are not given, a new figure with a single axes is created.
    :param ax: Axes to set up, e.g. a subplot of a larger figure
    :return: Figure, axes and the extent of the axes
    :raises ValueError: If the axes are given without their figure
    """
    x_min = x[0]
    x_max = x[-1]
    y_min = y[0]
    y_max = y[-1]
    extent = (x_min, x_max, y_min, y_max)

    if ax is None:
        fig = Figure()
        ax = fig.add_subplot()
    elif fig is None:
        raise ValueError("The figure of the axes must be given together with the axes.")

    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_min, y_max)
    ax.set_xlabel(xlabel, fontsize=label_fontsize)
    ax.set_ylabel(ylabel, fontsize=label_fontsize)

    add_ticks(
        ax,
        x_min=x_min, x_max=x_max, y_min=y_min, y_max=y_max,
        xtickpos=xtickpos, ytickpos=ytickpos,
        xticklabels=xticklabels, yticklabels=yticklabels
    )
    return fig, ax, extent
