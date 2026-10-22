"""Figures with logarithmic axes."""

import typing as tp

from matplotlib.axes import Axes
from matplotlib.figure import Figure
import numpy as np

from ptplot.science import const
from ptplot.science.plot.ticks import add_ticks
import ptplot.science.type_hints as th
from ptplot.science.utils import atleast_2d

#: Markers of the highlighted points, see :py:func:`add_highlights`.
#: These have the same shape and therefore the same visual size.
HIGHLIGHT_MARKERS: tuple[str, ...] = ("^", "v", "<", ">")


def add_points(
        ax: Axes,
        x: th.FloatOrArrOrList1D2D,
        y: th.FloatOrArrOrList1D2D,
        labels: th.StrOrListOrNestedList | None = None,
        titles: th.StrOrList | None = None) -> tuple[th.ArrOrListOfArrs, th.ArrOrListOfArrs]:
    r"""Add points to a $(\alpha, \beta/H)$ plot."""
    x2, y2 = atleast_2d(x, y)
    labels = nested_labels(labels)

    # Iterate over scenarios
    for i, (x_set, y_set) in enumerate(zip(x2, y2, strict=True)):
        x_log_set = np.log10(x_set)
        y_log_set = np.log10(y_set)

        # Plot points
        ax.plot(x_log_set, y_log_set, ".")
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
        x: th.FloatOrArrOrList1D2D,
        y: th.FloatOrArrOrList1D2D,
        highlights: dict[str, int]) -> None:
    r"""Highlight some of the points of a plot with logarithmic values on linear axes, e.g. an SNR figure.

    Each highlighted point is drawn with a marker of its own, which is added to the legend with its label.
    The existing entries of the legend, e.g. those of :py:func:`add_points`, are kept.

    :param ax: Axes to draw on
    :param x: x values of all the points [scenario, point]
    :param y: y values of all the points [scenario, point]
    :param highlights: Labels of the highlighted points, and their indices in the flattened points,
        see :py:func:`flat_points`
    """
    x_flat, y_flat = flat_points(x, y)
    legend = ax.get_legend()
    handles: list[tp.Any] = [] if legend is None else list(legend.legend_handles)
    labels: list[str] = [] if legend is None else [text.get_text() for text in legend.get_texts()]
    for i, (label, index) in enumerate(highlights.items()):
        handles += ax.plot(
            np.log10(x_flat[index]), np.log10(y_flat[index]),
            marker=HIGHLIGHT_MARKERS[i % len(HIGHLIGHT_MARKERS)], markersize=10,
            color="red", markeredgecolor="black", linestyle="none", zorder=10
        )
        labels.append(label)
    ax.legend(handles, labels, loc="lower left", framealpha=0.9)


def flat_points(
        x: th.FloatOrArrOrList1D2D,
        y: th.FloatOrArrOrList1D2D) -> tuple[th.FloatArr1D, th.FloatArr1D]:
    """Flatten the points [scenario, point] to 1D arrays, in which the scenarios follow each other.

    :param x: x values of the points [scenario, point]
    :param y: y values of the points [scenario, point]
    :return: Flattened x and y values
    """
    x2, y2 = atleast_2d(x, y)
    return np.concatenate([np.ravel(x_set) for x_set in x2]), np.concatenate([np.ravel(y_set) for y_set in y2])


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
