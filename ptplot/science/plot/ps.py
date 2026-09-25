#!/usr/bin/env python3

"""Power spectrum plotting."""

import os.path
import sys
import typing as tp

from matplotlib import rc_context
from matplotlib.figure import Figure
from pttools.utils.formatting import as_latex

if __name__ == "__main__" and __package__ is None:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from ptplot.science import const
from ptplot.science.noise import Noise, resolve_noise
from ptplot.science.parsing import PTPlotParser
from ptplot.science.plot.lock import matplotlib_lock
from ptplot.science.plot.utils import add_text, fig_to_svg, watermark
from ptplot.science.spectrum import PowerSpectrum, PowerSpectrumBPL2020, power_spectrum

#: Line style of the turbulence curves, when multiple spectra are drawn in the same figure.
TURB_LINESTYLE: str = "--"
#: Line style of the total curves, when multiple spectra are drawn in the same figure.
TOTAL_LINESTYLE: str = ":"


@matplotlib_lock
def power_spectrum_figure(
        spectra: PowerSpectrum | tp.Iterable[PowerSpectrum],
        noise: Noise | None = None,
        sw_only: bool = True) -> Figure:
    r"""Produce the power spectrum plot.

    The engine of each spectrum is printed in the legend.
    When multiple spectra are drawn, each of them is drawn with the color of its engine,
    and the components of a spectrum are distinguished from each other by their line styles.

    :param spectra: power spectrum, or multiple power spectra to be drawn in the same figure
    :param noise: Which noise curve to use
    :param sw_only: Whether to ignore turbulence
    :return: Power spectrum figure
    :raises ValueError: If no spectra were given
    """
    spectra_list: list[PowerSpectrum] = [spectra] if isinstance(spectra, PowerSpectrum) else list(spectra)
    if not spectra_list:
        raise ValueError("Got no power spectra to plot.")
    # Whether the figure contains multiple spectra, which have to be distinguished from each other
    multiple = len(spectra_list) > 1

    noise = resolve_noise(noise)

    with rc_context(const.DEFAULT_RC_CONTEXT):
        # You can increase the font size by also setting these in rc_params:
        # "font.size": 16
        # "legend.fontsize": 14

        fig = Figure()
        ax = fig.add_subplot()

        ax.fill_between(noise.f, noise.noise, 1, alpha=0.3, label=r"LISA noise")

        snr_texts: list[str] = []
        for spectrum in spectra_list:
            pow_spec, snr_value = spectrum.power_spectrum(noise.f, noise=noise)
            snr_latex = as_latex(snr_value, math_mode=True)
            snr_texts.append(f"SNR({spectrum.SHORT_NAME})={snr_latex}" if multiple else f"SNR={snr_latex}")
            # The engine is printed in the legend to tell the spectra apart.
            label_suffix = f" ({spectrum.SHORT_NAME})"
            color = spectrum.COLOR if multiple else ("k" if sw_only else "r")

            ax.plot(
                noise.f, pow_spec, color=color,
                label=r"$\Omega_\mathrm{sw}$" + label_suffix
            )
            if not sw_only and isinstance(spectrum, PowerSpectrumBPL2020):
                ax.plot(
                    noise.f, spectrum.power_spectrum_turb(noise.f),
                    color=color if multiple else "b",
                    linestyle=TURB_LINESTYLE if multiple else "-",
                    label=r"$\Omega_\mathrm{turb}$" + label_suffix
                )
                ax.plot(
                    noise.f, spectrum.power_spectrum_full_conservative(noise.f),
                    color=color if multiple else "k",
                    linestyle=TOTAL_LINESTYLE if multiple else "-",
                    label="Total" + label_suffix
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

        # With several spectra the SNR values are put on their own line, so that they fit in the figure.
        text = f"{watermark()}, {snr_texts[0]}" if not multiple \
            else "\n".join([watermark(), ", ".join(snr_texts)])
        add_text(fig, text)
    return fig


def main():
    """Write a power spectrum figure to stdout as an SVG."""
    parser = PTPlotParser(
        description="Writes a scalable vector graphic to stdout.",
        engines=True
    )
    args = parser.parse_args()
    spectra = [
        power_spectrum(
            v_wall=args.v_wall, alpha=args.alpha, beta_tilde=args.BetaoverH,
            T_star=args.Tstar, g_star=args.gstar,
            engine=engine
        )
        for engine in args.engine
    ]
    fig = power_spectrum_figure(spectra)
    print(fig_to_svg(fig).decode("utf-8"))


if __name__ == "__main__":
    main()
