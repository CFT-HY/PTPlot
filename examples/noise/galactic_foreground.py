r"""
Galactic foreground and the SNR contours
========================================

The galactic compact binary foreground dominates the LISA noise at 0.3-3 mHz,
and therefore sets the SNR of the BPL2020 spectra with $r_* \sim 0.01-0.1$ for $T_* = 100 \ \text{GeV}$.
This example shows how sensitive the SNR is to the model of the foreground,
using the variants of :py:mod:`examples.noise.foreground_utils`:
the sign of $\beta$ of :schmitz_2020:`\ `, a scaling factor of $\sqrt{2}$, other observation times,
the fit of :babak_2021:`\ ` and the extragalactic foreground divided by $\sqrt{2}$.

The first figure shows the SNR of each variant relative to the current PTPlot default
as a function of $r_*$, which is independent of $\bar{U}_f$.
The second figure shows the contours without the galactic foreground, with the default one,
and with the sign-corrected foreground scaled by $\sqrt{2}$.
"""

import logging

import matplotlib.pyplot as plt
import numpy as np

from examples.noise.foreground_utils import S_gal_babak, S_gb_cornish, noise_with_foreground
from examples.utils import save_fig
from ptplot.methods import setup_django

if __name__ == "__main__":
    setup_django()

from ptplot.science import const
from ptplot.science.noise import Noise
from ptplot.science.plot.snr import COLOR_TUPLE, LEVELS
from ptplot.science.snr.grid_ubarf_rstar import SNRGridUbarfRStar
from ptplot.science.spectrum.engine import Engine
import ptplot.science.type_hints as th

logger = logging.getLogger(__name__)

T_STAR: float = 100.
G_STAR: float = 100.
OBS_YEARS: float = 3.
DEFAULT_NAME: str = "PTtools default (ins + eb + gb)"


def noise_variants() -> dict[str, Noise]:
    """Create the noise curves with the variants of the galactic foreground."""
    f = Noise(obs_years=OBS_YEARS).f
    sqrt2 = np.sqrt(2)
    return {
        DEFAULT_NAME: noise_with_foreground(OBS_YEARS, s_gb=S_gb_cornish(f)),
        r"gb, sign of $\beta$ corrected": noise_with_foreground(OBS_YEARS, s_gb=S_gb_cornish(f, beta_sign=-1)),
        r"gb $\times\sqrt{2}$": noise_with_foreground(OBS_YEARS, s_gb=S_gb_cornish(f), gb_factor=sqrt2),
        r"gb, sign corrected, $\times\sqrt{2}$": noise_with_foreground(
            OBS_YEARS, s_gb=S_gb_cornish(f, beta_sign=-1), gb_factor=sqrt2
        ),
        "gb, 2-year parameters": noise_with_foreground(OBS_YEARS, s_gb=S_gb_cornish(f, t_obs=2.)),
        rf"gb of Babak et al., {OBS_YEARS:g} yr, $\times\sqrt{{2}}$": noise_with_foreground(
            OBS_YEARS, s_gb=S_gal_babak(f, t_obs=OBS_YEARS), gb_factor=sqrt2
        ),
        r"gb of Babak et al., 4 yr, $\times\sqrt{2}$": noise_with_foreground(
            OBS_YEARS, s_gb=S_gal_babak(f, t_obs=4.), gb_factor=sqrt2
        ),
        r"eb $/\sqrt{2}$": noise_with_foreground(OBS_YEARS, s_gb=S_gb_cornish(f), eb_factor=1 / sqrt2),
        "no gb (ins + eb)": noise_with_foreground(OBS_YEARS, s_gb=None),
    }


def snr_grid(noise: Noise) -> th.FloatArr2D:
    r"""Compute the BPL2020 SNR grid on the default $(\bar{U}_f, r_*)$ grid."""
    return SNRGridUbarfRStar(
        v_wall=const.DEFAULT_V_WALL, T_star=T_STAR, g_star=G_STAR,
        ubarf=const.DEFAULT_UBARF_RANGE, r_star=const.DEFAULT_R_STAR_RANGE,
        noise=noise, engine=Engine.BPL2020, log_progress_percentage=None
    ).snr


def main():
    """Plot the SNR with the variants of the galactic foreground."""
    noises = noise_variants()
    default = Noise(obs_years=OBS_YEARS)
    np.testing.assert_allclose(noises[DEFAULT_NAME].noise, default.noise, rtol=1e-12)
    grids = {name: snr_grid(noise) for name, noise in noises.items()}
    snr_default = grids[DEFAULT_NAME]
    r_star = const.DEFAULT_R_STAR_RANGE

    fig1, ax = plt.subplots(figsize=(7, 4.5))
    for name, snr in grids.items():
        ratio = (snr / snr_default)[:, 0]
        logger.info(
            "%s: SNR / default from %.3g (at r*=%.3g) to %.3g (at r*=%.3g)",
            name, ratio.min(), r_star[np.argmin(ratio)], ratio.max(), r_star[np.argmax(ratio)]
        )
        ax.semilogx(r_star, ratio, label=name)
    ax.set_xlabel(r"$r_*$")
    ax.set_ylabel(r"$\mathrm{SNR} / \mathrm{SNR}_\mathrm{default}$")
    ax.set_title(rf"BPL2020, $T_*={T_STAR:g}$ GeV, {OBS_YEARS:g} yr", fontsize=9)
    ax.grid(True, which="both", alpha=0.3)
    ax.legend(fontsize=7)
    fig1.tight_layout()
    save_fig(fig1, "noise_galactic_foreground_ratio")

    x = np.log10(const.DEFAULT_UBARF_RANGE)
    y = np.log10(r_star)
    fig2, ax = plt.subplots(figsize=(6, 5))
    ax.contour(x, y, grids["no gb (ins + eb)"], LEVELS, colors=COLOR_TUPLE, linewidths=0.8, linestyles="dotted")
    ax.contour(x, y, snr_default, LEVELS, colors=COLOR_TUPLE, linewidths=1, linestyles="dashed")
    contours = ax.contour(
        x, y, grids[r"gb, sign corrected, $\times\sqrt{2}$"], LEVELS, colors=COLOR_TUPLE, linewidths=1.3
    )
    ax.clabel(contours, fmt="%.0f", fontsize=7)
    ax.plot([], [], "k:", label="no gb")
    ax.plot([], [], "k--", label="gb, PTtools default")
    ax.plot([], [], "k-", label=r"gb, sign corrected, $\times\sqrt{2}$")
    ax.legend(fontsize=7, loc="lower left")
    ax.set_xlabel(r"$\log_{10} \bar{U}_f$")
    ax.set_ylabel(r"$\log_{10} r_*$")
    ax.set_title(rf"BPL2020 SNR contours, $T_*={T_STAR:g}$ GeV, {OBS_YEARS:g} yr", fontsize=9)
    fig2.tight_layout()
    save_fig(fig2, "noise_galactic_foreground_contours")


if __name__ == "__main__":
    main()
