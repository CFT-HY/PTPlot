"""Comparison of the SNR values given by different engines."""

from matplotlib.figure import Figure
import numpy as np

from ptplot.science.plot.logarithmic import add_points, log_figure
from ptplot.science.snr.grid import SNRGrid
import ptplot.science.type_hints as th


def snr_comparison(
        grid1: SNRGrid,
        grid2: SNRGrid,
        labels: th.StrOrListOrNestedList | None = None,
        titles: th.StrOrList | None = None) -> Figure:
    """Compare the SNR values given by different engines.

    :param grid1: SNR grid of the reference engine
    :param grid2: SNR grid of the engine to compare to the reference
    :param labels: Labels for the points, defaults to those of the first grid
    :param titles: Titles for the scenarios, defaults to those of the first grid
    :return: Figure of the relative difference of the SNR values
    """
    if grid1.X_NAME != grid2.X_NAME or grid1.Y_NAME != grid2.Y_NAME:
        raise ValueError(
            "SNR grids must have the same axes. "
            f"Got: grid1=({grid1.X_NAME}, {grid1.Y_NAME}), ({grid2.X_NAME}, {grid2.Y_NAME})"
        )
    if grid1.x.shape != grid2.x.shape or grid1.y.shape != grid2.y.shape \
            or not np.allclose(grid1.x, grid2.x) or not np.allclose(grid1.y, grid2.y):
        raise ValueError("SNR grids must have the same ranges.")

    fig, ax, extent = log_figure(
        x=np.log10(grid1.x),
        y=np.log10(grid1.y),
        xlabel=grid1.X_LABEL,
        ylabel=grid1.Y_LABEL
    )
    snr_rel_diff = (grid2.snr - grid1.snr) / np.maximum(grid1.snr, grid2.snr)
    contour = ax.contourf(snr_rel_diff, extent=extent)
    fig.colorbar(
        contour,
        ax=ax,
        label=
            rf"$\frac{{\text{{SNR}}_{{{grid2.engine.name}}} - \text{{SNR}}_{{{grid1.engine.name}}}}}"
            rf"{{\max( \text{{SNR}}_{{{grid1.engine.name}}}, \text{{SNR}}_{{{grid2.engine.name}}} )}}$"
    )
    if grid1.has_points:
        x_points, y_points = grid1.points()
        add_points(
            ax,
            x=x_points, y=y_points,
            labels=grid1.labels_points if labels is None else labels,
            titles=grid1.titles if titles is None else titles
        )
    return fig
