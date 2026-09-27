r"""
Noise curves: old and new
=========================

Compare the old precomputed LISA sensitivity curve with the PTtools noise curves that PTPlot uses now.

The first figure shows the noise components and the galactic foreground variants of
:py:mod:`examples.noise.foreground_utils`, together with the peak frequencies of the BPL2020 spectrum
$f_p = 26 \ \mu\text{Hz} \, (T_* / 100 \ \text{GeV}) / r_*$ for a few values of $r_*$,
which show which part of the noise curve sets the SNR at each $r_*$.
The second figure shows the ratio of the new and the old noise.
Without the compact binary foregrounds, it is the constant
:py:data:`ptplot.tests.test_noise.SENSITIVITY_FILE_FACTOR` at low frequencies,
and oscillates above the transfer frequency because of the exact LISA response.
"""

import logging

import matplotlib.pyplot as plt
import numpy as np
from pttools.omgw0.noise import omega_eb_h2, omega_h2, omega_ins_h2

from examples.noise.foreground_utils import S_gal_babak, S_gb_cornish
from examples.utils import save_fig
from ptplot.methods import setup_django

if __name__ == "__main__":
    setup_django()

from ptplot.science.noise import Noise
from ptplot.tests.old_ptplot import OLD_OBS_YEARS, OLD_SENSITIVITY_FILE
from ptplot.tests.test_noise import SENSITIVITY_FILE_FACTOR, load_sensitivity

logger = logging.getLogger(__name__)

#: $T_*$ for the peak frequency markers
T_STAR: float = 100.
#: $r_*$ values for the peak frequency markers
R_STARS: tuple[float, ...] = (1e-3, 1e-2, 3e-2, 1e-1, 1.)


def main():
    """Plot the noise curves and their ratios to the old sensitivity curve."""
    f_old, om_old = load_sensitivity(OLD_SENSITIVITY_FILE)
    noise = Noise(obs_years=OLD_OBS_YEARS)
    f = noise.f

    fig1, ax = plt.subplots(figsize=(7, 4.5))
    ax.loglog(f_old, om_old, "k--", label=f"old {OLD_SENSITIVITY_FILE}.txt")
    ax.loglog(f, omega_ins_h2(f), label="PTtools instrument (ins)")
    ax.loglog(f, omega_eb_h2(f), label="PTtools extragalactic binaries (eb)")
    ax.loglog(f, omega_h2(f=f, S=S_gb_cornish(f)), label=r"PTtools galactic binaries (gb), 4 yr")
    ax.loglog(f, omega_h2(f=f, S=S_gb_cornish(f, beta_sign=-1)), ":", label=r"gb, sign of $\beta$ corrected")
    ax.loglog(
        f, omega_h2(f=f, S=S_gal_babak(f, t_obs=OLD_OBS_YEARS)), "-.",
        label=f"gb of Babak et al. (2021), {OLD_OBS_YEARS:g} yr"
    )
    ax.loglog(f, noise.noise, "k", lw=1.5, label="ins + eb + gb (PTPlot default)")
    for r_star in R_STARS:
        f_peak = 26e-6 / r_star * T_STAR / 100
        ax.axvline(f_peak, color="grey", lw=0.5)
        ax.text(f_peak, 3e-8, rf"$r_*={r_star:g}$", rotation=90, fontsize=6, va="top")
    ax.set_xlim(1e-5, 1)
    ax.set_ylim(1e-16, 1e-7)
    ax.set_xlabel(r"$f$ (Hz)")
    ax.set_ylabel(r"$h^2 \Omega$")
    ax.set_title(rf"Noise curves; vertical lines: BPL2020 peak for $T_*={T_STAR:g}$ GeV", fontsize=9)
    ax.legend(fontsize=7)
    fig1.tight_layout()
    save_fig(fig1, "noise_curves")

    om_old_interp = 10**np.interp(np.log10(f), np.log10(f_old), np.log10(om_old))
    fig2, ax = plt.subplots(figsize=(7, 4))
    ax.semilogx(f, omega_ins_h2(f) / om_old_interp, label="PTtools ins / old")
    ax.semilogx(f, noise.noise / om_old_interp, label="PTtools ins + eb + gb / old")
    ax.axhline(SENSITIVITY_FILE_FACTOR, color="grey", ls="--", lw=0.8, label="SENSITIVITY_FILE_FACTOR")
    ax.set_yscale("log")
    ax.set_xlabel(r"$f$ (Hz)")
    ax.set_ylabel("noise ratio")
    ax.grid(True, which="both", alpha=0.3)
    ax.legend(fontsize=8)
    fig2.tight_layout()
    save_fig(fig2, "noise_ratio")

    ratio = noise.noise / om_old_interp
    i_max = np.argmax(ratio)
    logger.info(
        "The total noise is at most %.3g times the old curve, at f=%.3g Hz. "
        "The instrument noise alone is %.4g times the old curve at 0.1 mHz.",
        ratio[i_max], f[i_max], np.interp(1e-4, f, omega_ins_h2(f) / om_old_interp)
    )


if __name__ == "__main__":
    main()
