#!/usr/bin/env python3

r"""Create the $\bar{U}_f-R_*$ plot.

This file contains all the functions related to producing the $\bar{U}_f-R_*$ plot.
Broken power law by Mark Hindmarsh (Sep 2015), inspired by Antoine Petiteau's
ExampleUseSNR1.py v0.3 (May 2015). SNR plots for PTPlot by David Weir (Feb 2018).
"""

from pathlib import Path
import sys
import typing as tp

if __name__ == "__main__" and __package__ is None:
    sys.path.append(str(Path(__file__).resolve().parents[3]))

from ptplot.science.noise import noise_curve
from ptplot.science.parsing import PTPlotParser
from ptplot.science.plot.snr import SNRFigure
from ptplot.science.plot.utils import fig_to_svg
from ptplot.science.snr.grid_ubarf_rstar import SNRGridUbarfRStar


class SNRFigureUbarfRStar(SNRFigure):
    r"""SNR figure of $(\bar{U}_f, r_*)$."""

    LABEL_WANTED_Y = -2.5

    def __init__(self, grid: SNRGridUbarfRStar, **kwargs: tp.Any):
        r"""Set up the SNR figure of $(\bar{U}_f, r_*)$.

        :param grid: Precomputed SNR grid
        :param kwargs: Arguments of :py:class:`~ptplot.science.plot.snr.SNRFigure`
        """
        super().__init__(grid=grid, **kwargs)

    def default_shock_label_locs(self) -> list[tuple[float, float]]:
        r"""Locations of the $\mathcal{H}_* \eta_\text{sh}$ contour labels in the Matplotlib figure.

        :return: A label for each integer power of ten on the y-axis, staggered along the x-axis
        """
        x_mid = (self.x_log10[0] + self.x_log10[-1]) / 2
        return [(x_mid + 0.2 - 0.2 * i, float(y)) for i, y in enumerate(self.y_decades())]


def main() -> None:
    """Script for command-line use."""
    parser = PTPlotParser(
        description="Writes a scalable vector graphic to stdout.",
        noise=True,
        engine=True
    )
    args = parser.parse_args()
    noise = noise_curve(obs_years=args.obs_years, eb=args.noise_eb, gb=args.noise_gb)
    fig = SNRFigureUbarfRStar(
        grid=SNRGridUbarfRStar(
            v_wall=args.v_wall, T_star=args.Tstar, g_star=args.gstar,
            alpha_points=args.alpha, beta_tilde_points=args.BetaoverH, v_wall_points=args.v_wall,
            noise=noise, engine=args.engine
        )
    ).matplotlib()
    print(fig_to_svg(fig).decode("utf-8"))


if __name__ == "__main__":
    main()
