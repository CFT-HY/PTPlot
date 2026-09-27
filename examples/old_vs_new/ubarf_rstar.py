r"""
SNR on the $(\bar{U}_f, r_*)$ plane: old and new
================================================

Decompose the change of the BPL2020 SNR contours between the old PTPlot and the current one
by changing one ingredient at a time: the noise components and the code.

The old grid is computed with the old PTPlot, if it is found (please see :py:mod:`ptplot.tests.old_ptplot`),
and is otherwise reconstructed with :py:func:`ptplot.tests.old_ptplot.reconstructed_old_grid`.

At fixed $r_*$ the BPL2020 spectrum only changes its amplitude with $\bar{U}_f$.
Therefore, any change of the noise curve rescales the SNR by a factor that depends only on $r_*$,
and a factor that depends on $r_*$ changes the shape of the contours.
The first figure shows this factor for each noise combination.
"""

import logging

import matplotlib.pyplot as plt
import numpy as np

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
from ptplot.tests.old_ptplot import OLD_OBS_YEARS, old_or_reconstructed_grid, snr_factor

logger: logging.Logger = logging.getLogger(__name__)

T_STAR: float = 100.
G_STAR: float = 100.
#: The noise combinations: (extragalactic binaries, galactic binaries)
NOISE_COMPONENTS: tuple[tuple[bool, bool], ...] = ((False, False), (True, False), (False, True), (True, True))


def noise_label(eb: bool, gb: bool) -> str:
    """Label of a noise combination."""
    return "ins" + (" + eb" if eb else "") + (" + gb" if gb else "")


def new_grid(noise: Noise, ubarf: th.FloatArr1D, r_star: th.FloatArr1D) -> th.FloatArr2D:
    r"""Compute the BPL2020 SNR grid with the current code."""
    return SNRGridUbarfRStar(
        v_wall=const.DEFAULT_V_WALL, T_star=T_STAR, g_star=G_STAR, ubarf=ubarf, r_star=r_star,
        noise=noise, engine=Engine.BPL2020, log_progress_percentage=None
    ).snr


def contour_comparison(
        x: th.FloatArr1D,
        y: th.FloatArr1D,
        snr1: th.FloatArr2D,
        snr2: th.FloatArr2D,
        label1: str,
        label2: str,
        path: str) -> None:
    """Draw the SNR contours of two grids in the same figure."""
    fig, ax = plt.subplots(figsize=(6, 5))
    ax.contour(x, y, snr1, LEVELS, colors=COLOR_TUPLE, linewidths=1, linestyles="dashed")
    contours = ax.contour(x, y, snr2, LEVELS, colors=COLOR_TUPLE, linewidths=1.3)
    ax.clabel(contours, fmt="%.0f", fontsize=7)
    ax.plot([], [], "k--", label=label1)
    ax.plot([], [], "k-", label=label2)
    ax.legend(fontsize=7, loc="lower left")
    ax.set_xlabel(r"$\log_{10} \bar{U}_f$")
    ax.set_ylabel(r"$\log_{10} r_*$")
    ax.set_title(f"BPL2020 SNR contours, $T_*={T_STAR:g}$ GeV, {OLD_OBS_YEARS:g} yr", fontsize=9)
    fig.tight_layout()
    save_fig(fig, path)


def main() -> None:
    r"""Compare the old and the new SNR grids on the $(\bar{U}_f, r_*)$ plane."""
    (_, snr_old, log10_r_star, log10_ubarf), from_old_code = old_or_reconstructed_grid(T_STAR, G_STAR)
    old_label = "old code, old noise" if from_old_code else "old noise (reconstructed)"
    ubarf = 10**log10_ubarf
    r_star = 10**log10_r_star

    grids = {
        noise_label(eb, gb): new_grid(Noise(obs_years=OLD_OBS_YEARS, eb=eb, gb=gb), ubarf=ubarf, r_star=r_star)
        for eb, gb in NOISE_COMPONENTS
    }
    for label, snr in grids.items():
        ratio = snr / snr_old
        # The ratio should depend only on r_star.
        variation = np.nanmax(np.nanmax(ratio, axis=1) / np.nanmin(ratio, axis=1)) - 1
        logger.info(
            "SNR(%s) / SNR(%s): min=%.4g, max=%.4g, max relative variation along ubarf=%.2g",
            label, old_label, np.nanmin(ratio), np.nanmax(ratio), variation
        )

    fig, ax = plt.subplots(figsize=(7, 4.5))
    for label, snr in grids.items():
        ax.plot(r_star, (snr / snr_old)[:, 0], label=f"new code, {label}")
    ax.axhline(snr_factor(G_STAR), color="k", ls="--", lw=0.8, label="constant factors only")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel(r"$r_* = H_* R_*$")
    ax.set_ylabel(rf"$\mathrm{{SNR}} / \mathrm{{SNR}}_\mathrm{{old}}$ ({old_label})")
    ax.set_title(rf"BPL2020, $T_*={T_STAR:g}$ GeV, $g_*={G_STAR:g}$, {OLD_OBS_YEARS:g} yr", fontsize=9)
    ax.grid(True, which="both", alpha=0.3)
    ax.legend(fontsize=7)
    fig.tight_layout()
    save_fig(fig, "old_vs_new_ubarf_rstar_ratio")

    comparisons = (
        (snr_old, grids["ins + eb + gb"], old_label, "new code, ins + eb + gb (default)", "default"),
        (snr_old, grids["ins"], old_label, "new code, ins", "ins"),
        (grids["ins"], grids["ins + eb + gb"], "new code, ins", "new code, ins + eb + gb", "ins_vs_full"),
        (grids["ins + eb"], grids["ins + eb + gb"], "new code, ins + eb", "new code, ins + eb + gb", "eb_vs_full"),
    )
    for snr1, snr2, label1, label2, name in comparisons:
        contour_comparison(
            log10_ubarf, log10_r_star, snr1, snr2, label1=label1, label2=label2,
            path=f"old_vs_new_ubarf_rstar_contours_{name}"
        )


if __name__ == "__main__":
    main()
