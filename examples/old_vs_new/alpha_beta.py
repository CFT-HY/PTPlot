r"""
SNR on the $(\alpha, \beta/H_*)$ plane: old and new
===================================================

Compare the BPL2020 SNR contours on the $(\alpha, \beta/H_*)$ plane of the old PTPlot and the current one
for several wall speeds.

The old PTPlot computed the grid on the $(\bar{U}_f, r_*)$ plane and converted the axes to $(\alpha, \beta/H_*)$
with the legacy $\max(v_{\text{wall}}, c_s)$ (please see :py:func:`ptplot.tests.old_ptplot.old_alpha_beta_axes`),
whereas the current PTPlot computes the grid on the $(\alpha, \beta/H_*)$ plane directly.
The old grid is computed with the old PTPlot, if it is found, and is otherwise reconstructed
(please see :py:func:`ptplot.tests.old_ptplot.old_or_reconstructed_grid`).

The upper row compares the old contours with the current default ones.
The lower row separates the effects of the code and of the noise:
the current code with the old sensitivity curve, with and without the legacy $\max(v_{\text{wall}}, c_s)$,
and with the PTtools instrument noise.
For $v_{\text{wall}} \geq c_s$, the code with the old sensitivity curve reproduces the old contours,
and for $v_{\text{wall}} < c_s$ it does so only with the legacy conversion.
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
from ptplot.science.snr.grid_alpha_beta import SNRGridAlphaBeta
from ptplot.science.spectrum.engine import Engine
import ptplot.science.type_hints as th
from ptplot.tests.old_ptplot import (
    OLD_OBS_YEARS,
    OLD_UBARF_MAX_ALPHA_BETA,
    f_gw0_ratio,
    old_alpha_beta_axes,
    old_file_noise,
    old_or_reconstructed_grid,
)

logger: logging.Logger = logging.getLogger(__name__)

T_STAR: float = 180.
G_STAR: float = 100.
V_WALLS: tuple[float, ...] = (0.3, 0.5, 0.7, 0.9, 0.95)


def new_grid(v_wall: float, noise: Noise, legacy: bool = False) -> th.FloatArr2D:
    r"""Compute the BPL2020 SNR grid on the default $(\alpha, \beta/H_*)$ grid with the current code."""
    return SNRGridAlphaBeta(
        T_star=T_STAR, g_star=G_STAR, v_wall=v_wall,
        alpha_n=const.DEFAULT_ALPHA_N_RANGE, beta_tilde=const.DEFAULT_beta_tilde_RANGE,
        noise=noise, engine=Engine.BPL2020, log_progress_percentage=None,
        legacy_nucleation_cs_max=legacy
    ).snr


def main() -> None:
    r"""Plot the old and the new SNR contours on the $(\alpha, \beta/H_*)$ plane."""
    (_, snr_old, log10_r_star, log10_ubarf), from_old_code = old_or_reconstructed_grid(
        T_STAR, G_STAR, OLD_UBARF_MAX_ALPHA_BETA
    )
    old_label = "old code" if from_old_code else "old (reconstructed)"
    noise_old = old_file_noise()
    noise_ins = Noise(obs_years=OLD_OBS_YEARS, eb=False, gb=False)
    noise_full = Noise(obs_years=OLD_OBS_YEARS)
    x = np.log10(const.DEFAULT_ALPHA_N_RANGE)
    y = np.log10(const.DEFAULT_beta_tilde_RANGE)

    fig, axs = plt.subplots(2, len(V_WALLS), figsize=(4 * len(V_WALLS), 8), sharex=True, sharey=True)
    for i, v_wall in enumerate(V_WALLS):
        alpha_old, beta_tilde_old = old_alpha_beta_axes(v_wall, log10_ubarf=log10_ubarf, log10_r_star=log10_r_star)
        x_old = np.log10(alpha_old)
        y_old = np.log10(beta_tilde_old)
        # The old sensitivity curve with the old F_gw0, to isolate the effect of the code
        snr_old_noise = new_grid(v_wall, noise_old) / f_gw0_ratio(G_STAR)
        snr_old_noise_legacy = new_grid(v_wall, noise_old, legacy=True) / f_gw0_ratio(G_STAR)
        snr_ins = new_grid(v_wall, noise_ins)
        snr_full = new_grid(v_wall, noise_full)
        logger.info(
            "v_wall=%s: legacy / default conversion with the old noise: SNR ratio %.3g to %.3g",
            v_wall, np.nanmin(snr_old_noise_legacy / snr_old_noise), np.nanmax(snr_old_noise_legacy / snr_old_noise)
        )

        ax = axs[0, i]
        ax.contour(x_old, y_old, snr_old, LEVELS, colors=COLOR_TUPLE, linewidths=1, linestyles="dashed")
        contours = ax.contour(x, y, snr_full, LEVELS, colors=COLOR_TUPLE, linewidths=1.3)
        ax.clabel(contours, fmt="%.0f", fontsize=7)
        ax.set_title(rf"$v_\mathrm{{w}}={v_wall}$: {old_label} (dashed), new (solid)", fontsize=8)

        ax = axs[1, i]
        ax.contour(x_old, y_old, snr_old, LEVELS, colors=COLOR_TUPLE, linewidths=0.8, linestyles="dotted")
        ax.contour(x, y, snr_old_noise_legacy, LEVELS, colors=COLOR_TUPLE, linewidths=1, linestyles="dashdot")
        ax.contour(x, y, snr_old_noise, LEVELS, colors=COLOR_TUPLE, linewidths=1, linestyles="dashed")
        contours = ax.contour(x, y, snr_ins, LEVELS, colors=COLOR_TUPLE, linewidths=1.3)
        ax.clabel(contours, fmt="%.0f", fontsize=7)
        ax.set_title(
            f"{old_label} (dotted); new code with old noise:\n"
            "legacy (dash-dot), default (dashed); new code, ins (solid)",
            fontsize=7
        )
        for ax in axs[:, i]:
            ax.set_xlim(x[0], x[-1])
            ax.set_ylim(y[0], y[-1])
            ax.set_xlabel(r"$\log_{10} \alpha$")
    for ax in axs[:, 0]:
        ax.set_ylabel(r"$\log_{10} \beta/H_*$")
    fig.suptitle(rf"BPL2020, $T_*={T_STAR:g}$ GeV, $g_*={G_STAR:g}$, {OLD_OBS_YEARS:g} yr")
    fig.tight_layout()
    save_fig(fig, "old_vs_new_alpha_beta_contours")


if __name__ == "__main__":
    main()
