"""Figures with logarithmic axes."""

from matplotlib.axes import Axes
from matplotlib.figure import Figure
import numpy as np

from ptplot.science import const
from ptplot.science.plot.ticks import add_ticks
import ptplot.science.type_hints as th
from ptplot.science.utils import atleast_2d


def add_points(
        ax: Axes,
        x: th.FloatOrArrOrList1D2D,
        y: th.FloatOrArrOrList1D2D,
        labels: th.StrOrListOrNestedList | None = None,
        titles: th.StrOrList | None = None):
    r"""Add points to a $(\alpha, \beta/H)$ plot."""
    x2, y2 = atleast_2d(x, y)
    if labels:
        if isinstance(labels, str):
            labels = [[labels]]
        elif isinstance(labels[0], str):
            labels = [labels]

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


def log_figure(
        x: th.FloatArr1D,
        y: th.FloatArr1D,
        xlabel: str,
        ylabel: str,
        # fig: Figure = None,
        # ax: Axes = None,
        xtickpos: th.IntArr1D | None = None,
        ytickpos: th.IntArr1D | None = None,
        xticklabels: list[str] | None = None,
        yticklabels: list[str] | None = None,
        label_fontsize: int = const.DEFAULT_LABEL_FONTSIZE) -> tuple[Figure, Axes, tuple[float, float, float, float]]:
    """Create a figure that has logarithmic tick labels on linear axes."""
    x_min = x[0]
    x_max = x[-1]
    y_min = y[0]
    y_max = y[-1]
    extent = (x_min, x_max, y_min, y_max)

    fig = Figure()
    ax = fig.add_subplot()

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
