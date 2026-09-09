"""Comparison of the SNR values given by different engines or parameter values."""

from matplotlib.figure import Figure
from matplotlib.ticker import LogFormatterSciNotation
import numpy as np

from ptplot.science.plot.lock import matplotlib_lock
from ptplot.science.plot.logarithmic import add_points, log_figure
from ptplot.science.snr.grid_comparison import SNRGridComparison
import ptplot.science.type_hints as th


@matplotlib_lock
def snr_comparison(
        comparison: SNRGridComparison,
        labels: th.StrOrListOrNestedList | None = None,
        titles: th.StrOrList | None = None) -> Figure:
    """Draw the comparison of the SNR values of two grids.

    :param comparison: Comparison of the two SNR grids
    :param labels: Labels for the points, defaults to those of the first grid
    :param titles: Titles for the scenarios, defaults to those of the first grid
    :return: Figure of the compared SNR values
    """
    fig, ax, extent = log_figure(
        x=np.log10(comparison.x),
        y=np.log10(comparison.y),
        xlabel=comparison.X_LABEL,
        ylabel=comparison.Y_LABEL
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
    return fig
