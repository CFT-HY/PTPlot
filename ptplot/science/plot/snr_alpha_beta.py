r"""$(\alpha_n, \beta/H)$ plotting.

Inspired by Antoine Petiteau's ExampleUseSNR1.py v0.3 (May 2015).
"""

import os.path
import sys

from matplotlib.figure import Figure
import numpy as np

if __name__ == "__main__" and __package__ is None:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from ptplot.science.noise import noise_curve
from ptplot.science.parsing import PTPlotParser
from ptplot.science.plot.lock import matplotlib_lock
from ptplot.science.plot.logarithmic import add_points
from ptplot.science.plot.snr import snr_figure
from ptplot.science.plot.utils import fig_to_svg
from ptplot.science.snr.grid_alpha_beta import SNRGridAlphaBeta
import ptplot.science.type_hints as th


@matplotlib_lock
def snr_figure_alpha_beta(
        grid: SNRGridAlphaBeta,
        labels: th.StrOrListOrNestedList | None = None,
        titles: th.StrOrList | None = None,
        huge_alpha: bool = False,
        filled: bool = False) -> Figure:
    r"""Produce the $(\alpha_n, \beta/H)$ plot.

    :param grid: Precomputed SNR grid
    :param labels: Labels for the points, defaults to those of the grid
    :param titles: Titles for the scenarios, defaults to those of the grid
    :param huge_alpha: Whether $\alpha$ is very large
    :param filled: Whether to fill the contour plot
    :return: SNR figure of $(\alpha_n, \beta/H)$
    """
    log10_alpha_n_grid = np.log10(grid.alpha_n)
    log10_beta_over_H_grid = np.log10(grid.beta_over_H)
    alpha_mid = (log10_alpha_n_grid[0] + log10_alpha_n_grid[-1]) / 2

    fig, ax = snr_figure(
        grid=grid,
        shock_label_locs=[
            (alpha_mid - 0.3 + 0.2 * i, float(y))
            for i, y in enumerate(range(int(log10_beta_over_H_grid[0]), int(log10_beta_over_H_grid[-1]) + 1))
        ],
        label_wanted_y=2,
        huge_alpha=huge_alpha,
        filled=filled
    )
    if grid.has_points:
        alpha_points, beta_over_H_points = grid.points()
        add_points(
            ax=ax,
            x=alpha_points, y=beta_over_H_points,
            labels=grid.labels_points if labels is None else labels,
            titles=grid.titles if titles is None else titles
        )
    return fig


def main():
    """Script for command-line use."""
    parser = PTPlotParser(
        description="Writes a scalable vector graphic to stdout.",
        noise=True,
        engine=True
    )
    args = parser.parse_args()
    noise = noise_curve(obs_years=args.obs_years, eb=args.noise_eb, gb=args.noise_gb)
    fig = snr_figure_alpha_beta(
        grid=SNRGridAlphaBeta(
            v_wall=args.v_wall, T_star=args.Tstar, g_star=args.gstar,
            alpha_points=args.alpha, beta_over_H_points=args.BetaoverH,
            noise=noise, engine=args.engine
        )
    )
    print(fig_to_svg(fig).decode("utf-8"))


if __name__ == "__main__":
    main()
