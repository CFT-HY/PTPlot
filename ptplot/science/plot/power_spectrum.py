#!/usr/bin/env python3

"""Power spectrum plotting"""

import math
import os.path
import sys

from matplotlib import rc_context
from matplotlib.figure import Figure
import numpy as np
from pttools.omgw0 import signal_to_noise_ratio

if __name__ == "__main__" and __package__ is None:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from ptplot.science import const
from ptplot.science.parsing import PTPlotParser
from ptplot.science.plot.utils import add_text, fig_to_svg, watermark
from ptplot.science.spectrum import PowerSpectrum, PowerSpectrumBPL, PowerSpectrumSSM, power_spectrum
from ptplot.science.mission_profile import DEFAULT_MISSION_PROFILE, MissionProfile


def power_spectrum_figure(
        spectrum: PowerSpectrum,
        mission_profile: MissionProfile = DEFAULT_MISSION_PROFILE,
        sw_only: bool = True) -> Figure:
    r"""Produce the power spectrum plot

    :param spectrum: power spectrum
    :param mission_profile: Which sensitivity curve to use
    :param sw_only: Whether to ignore turbulence
    :return: Power spectrum figure
    """
    pow_spec = spectrum.power_spectrum(mission_profile.f)
    snr_value = signal_to_noise_ratio(
        f=mission_profile.f,
        signal=pow_spec,
        f_noise=mission_profile.f,
        noise=mission_profile.sensitivity,
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
        ax = fig.add_subplot()

        ax.fill_between(mission_profile.f, mission_profile.sensitivity, 1, alpha=0.3, label=r"LISA sensitivity")

        # Avoid expensive recomputation with the SSM
        if isinstance(spectrum, PowerSpectrumSSM):
            f2 = mission_profile.f
            pow_spec2 = pow_spec
        else:
            f2 = f_more
            pow_spec2 = spectrum.power_spectrum(f_more)

        ax.plot(
            f2, pow_spec2, "k" if sw_only else "r",
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

        add_text(fig, f"{watermark()}, SNR={snr_value:g}")
    return fig


def main():
    parser = PTPlotParser(
        description="Writes a scalable vector graphic to stdout.",
        engine=True
    )
    args = parser.parse_args()
    spectrum = power_spectrum(
        v_wall=args.vw, alpha=args.alpha, beta_over_H=args.BetaoverH,
        T_star=args.Tstar, g_star=args.gstar,
        engine=args.engine
    )
    fig = power_spectrum_figure(spectrum)
    print(fig_to_svg(fig).decode("utf-8"))


if __name__ == "__main__":
    main()
