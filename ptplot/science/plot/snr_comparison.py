"""Comparison of the SNR values given by different engines or parameter values."""

from collections.abc import Sequence

from matplotlib import rc_context
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.ticker import LogFormatterSciNotation
import numpy as np

from ptplot.science import const
from ptplot.science.plot.lock import matplotlib_lock
from ptplot.science.plot.logarithmic import add_highlights, add_points, log_figure
from ptplot.science.plot.utils import add_subplot_titles, subplot_grid
from ptplot.science.snr.grid_comparison import SNRGridComparison
import ptplot.science.type_hints as th


@matplotlib_lock
def snr_comparison(
        comparison: SNRGridComparison,
        labels: th.StrOrListOrNestedList | None = None,
        titles: th.StrOrList | None = None,
        highlights: dict[str, int] | None = None,
        fig: Figure | None = None,
        ax: Axes | None = None) -> Figure:
    """Draw the comparison of the SNR values of two grids.

    :param comparison: Comparison of the two SNR grids
    :param labels: Labels for the points, defaults to those of the first grid
    :param titles: Titles for the scenarios, defaults to those of the first grid
    :param highlights: Labels of the points of the first grid to be highlighted,
        and their indices in the flattened points, see :py:func:`ptplot.science.plot.logarithmic.add_highlights`
    :param fig: Figure of the axes, see :py:func:`ptplot.science.plot.logarithmic.log_figure`
    :param ax: Axes to draw on, e.g. a subplot of a larger figure, see :py:func:`snr_comparison_grid`
    :return: Figure of the compared SNR values
    """
    fig, ax, extent = log_figure(
        x=np.log10(comparison.x),
        y=np.log10(comparison.y),
        xlabel=comparison.X_LABEL_LATEX,
        ylabel=comparison.Y_LABEL_LATEX,
        fig=fig,
        ax=ax
    )
    contour = ax.contourf(
        comparison.snr_diff,
        extent=extent,
        levels=comparison.levels,
        norm=comparison.norm
    )
    fig.colorbar(
        contour,
        ax=ax,
        label=comparison.label,
        format=LogFormatterSciNotation() if comparison.norm is not None else None
    )
    grid1 = comparison.grid1
    if grid1.has_points:
        x_points, y_points = grid1.points()
        add_points(
            ax,
            x=x_points, y=y_points,
            labels=grid1.labels_points if labels is None else labels,
            titles=grid1.titles if titles is None else titles
        )
        if highlights:
            add_highlights(ax, x=x_points, y=y_points, highlights=highlights)
    return fig


@matplotlib_lock
def snr_comparison_grid(
        comparisons: Sequence[SNRGridComparison],
        subplot_titles: Sequence[str] | None = None,
        highlights: dict[str, int] | None = None,
        ncols: int = 2) -> Figure:
    """Draw several comparisons of SNR grids as the subplots of a single figure, e.g. those of different engines.

    :param comparisons: Comparisons of SNR grids
    :param subplot_titles: Titles of the subplots, defaults to the names of the compared grids
    :param highlights: Labels of the points to be highlighted, and their indices, see :py:func:`snr_comparison`
    :param ncols: Maximum number of columns of subplots
    :return: Figure of the compared SNR values
    """
    if subplot_titles is None:
        subplot_titles = [f"{comparison.grid2.name} vs. {comparison.grid1.name}" for comparison in comparisons]
    with rc_context(const.DEFAULT_RC_CONTEXT):
        fig, axs = subplot_grid(len(comparisons), ncols=ncols)
        for comparison, ax in zip(comparisons, axs, strict=True):
            snr_comparison(comparison, highlights=highlights, fig=fig, ax=ax)
        add_subplot_titles(fig, axs, subplot_titles)
    return fig
