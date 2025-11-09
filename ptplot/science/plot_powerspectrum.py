#!/usr/bin/env python3

"""Power spectrum plotting"""

import math
import os.path
import sys
import time

from matplotlib import rc_context
from matplotlib.figure import Figure
import numpy as np

if __name__ == "__main__" and __package__ is None:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ptplot.science import const, snr
from ptplot.science.parsing import PTPlotParser
from ptplot.science.plot_utils import add_text, fig_to_svg
from ptplot.science.spectrum import PowerSpectrum, PowerSpectrumBPL, power_spectrum
from ptplot.science.mission_profile import DEFAULT_MISSION_PROFILE, MissionProfile


def get_ps_data(
        spectrum: PowerSpectrumBPL,
        mission_profile: MissionProfile = DEFAULT_MISSION_PROFILE,
        sw_only: bool = True) -> str:
    r"""Retrieve the data for the power spectrum plot

    Note that this is not then used to create the plot, this stores the data,
    to be exported as a csv if requested.

    :param spectrum: power spectrum
    :param mission_profile: Which sensitivity curve to use
    :param sw_only: Whether to ignore turbulence
    :return: String containing all the data to reproduce the power spectrum plot
    """
    res = "f, omegaSens, omegaSW\n" if sw_only else "f, omegaSens, omegaSW, omegaTurb, omegaTot\n"

    for x, y in zip(mission_profile.f, mission_profile.sensitivity):
        if sw_only:
            res = res + "%g, %g, %g\n" % (x, y, spectrum.power_spectrum_sw_conservative(x))
        else:
            res = res + "%g, %g, %g, %g, %g\n" % (
                x, y,
                spectrum.power_spectrum_sw_conservative(x),
                spectrum.power_spectrum_turb(x),
                spectrum.power_spectrum_conservative(x)
            )
    return res


def get_ps_image(
        spectrum: PowerSpectrum,
        mission_profile: MissionProfile = DEFAULT_MISSION_PROFILE,
        sw_only: bool = True) -> Figure:
    r"""Produce the power spectrum plot

    :param spectrum: power spectrum
    :param mission_profile: Which sensitivity curve to use
    :param sw_only: Whether to ignore turbulence
    :return: Power spectrum figure
    """
    snr_value, frange = snr.stock_bkg_compute_snr(
        sens_freq=mission_profile.f,
        sens_omega=mission_profile.sensitivity,
        gw_freq= mission_profile.f,
        gw_omega=spectrum.power_spectrum(mission_profile.f),
        obs_time=mission_profile.duration_seconds,
        f_min=1.e-6,
        f_max=1
    )
    f_more = np.logspace(
        math.log(mission_profile.f_min),
        math.log(mission_profile.f_max),
        num=len(mission_profile.f) * 10
    )

    with rc_context(const.DEFAULT_RC_CONTEXT):
        # You can increase the font size by also setting these in rc_params:
        # "font.size": 16
        # "legend.fontsize": 14

        fig = Figure()
        ax = fig.add_subplot(111)

        ax.fill_between(mission_profile.f, mission_profile.sensitivity, 1, alpha=0.3, label=r"LISA sensitivity")

        ax.plot(
            f_more, spectrum.power_spectrum(f_more), "k" if sw_only else "r",
            label=r"$\Omega_\mathrm{sw}$"
        )
        if not sw_only and isinstance(spectrum, PowerSpectrumBPL):
            ax.plot(
                f_more, spectrum.power_spectrum_turb(f_more), "b",
                label=r"$\Omega_\mathrm{turb}$"
            )
            ax.plot(
                f_more, spectrum.power_spectrum_full_conservative(f_more), "k",
                label=r"Total"
            )

        ax.set_xlabel(r"$f\; \mathrm{(Hz)}$", fontsize=const.DEFAULT_LABEL_FONTSIZE)
        ax.set_ylabel(r"$h^2 \, \Omega_\mathrm{GW}(f)$", fontsize=const.DEFAULT_LABEL_FONTSIZE)
        ax.set_xlim(1e-5, 0.1)
        ax.set_ylim(1e-16, 1e-8)
        ax.set_yscale("log", nonpositive="clip")
        ax.set_xscale("log", nonpositive="clip")
        ax.legend(loc="upper right")

        # July 2023: No longer watermark with LISACosWG
        # # position bottom right
        # fig.text(0.95, 0.05, "LISACosWG",
        #          fontsize=50, color="gray",
        #          ha="right", va="bottom", alpha=0.4)

        add_text(fig, r"%s [$\mathrm{SNR}_\mathrm{sw} = %g$]" % (time.asctime(), snr_value))
    return fig


def main():
    parser = PTPlotParser(
        description="Writes a scalable vector graphic to stdout.",
        engine=True
    )
    args = parser.parse_args()
    spectrum = power_spectrum(
        vw=args.vw, alpha=args.alpha, beta_over_H=args.BetaoverH,
        T_star=args.Tstar, g_star=args.gstar,
        engine=args.engine
    )
    fig = get_ps_image(spectrum)
    print(fig_to_svg(fig).decode("utf-8"))


if __name__ == "__main__":
    main()
