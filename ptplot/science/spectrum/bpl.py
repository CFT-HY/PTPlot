"""Broken power law (BPL) power spectrum."""

import math
import typing as tp

from pandas import DataFrame

from ptplot.science import const
from ptplot.science.mission_profile import DEFAULT_MISSION_PROFILE, MissionProfile
from ptplot.science.spectrum.base import Engine, PowerSpectrum
import ptplot.science.type_hints as th


class PowerSpectrumBPL(PowerSpectrum):
    r"""Broken power law (BPL) power spectrum.

    Based on :hindmarsh_2017:`\ ` and `hindmarsh_2017_erratum:`\ `.
    Original design by Mark Hindmarsh (Sep 2015).

    Also contains functions for turbulence.
    However, in later papers the contribution from turbulence is neglected,
    as further studies to understand turbulence are needed.
    As such, the turbulence functions are not called anywhere in the code by default.
    However, they can still be turned on by overriding the sw_only flag.
    """

    COLOR = "red"
    ENGINE = Engine.BPL
    NAME = "Broken power law"
    SHORT_NAME = "BPL"

    def csv(
            self,
            path: str | None = None,
            mission_profile: MissionProfile = DEFAULT_MISSION_PROFILE,
            sw_only: bool = True) -> str | None:
        r"""Export the power spectrum as CSV.

        :param path: A path in which to save the data
        :param mission_profile: Which sensitivity curve to use
        :param sw_only: Whether to ignore turbulence
        :return: If a path is not given, the data will be returned as a string.
        """
        if sw_only:
            return super().csv(path=path, mission_profile=mission_profile)
        f = mission_profile.f
        return DataFrame({
            "f": f,
            "omegaSens": mission_profile.sensitivity,
            "omegaSW": self.power_spectrum(f),
            "omegaTurb": self.power_spectrum_turb(f),
            "omegaTot": self.power_spectrum_full_conservative(f)
        }).to_csv(path)

    @staticmethod
    def C(s: th.FloatOrArr, norm: float = 1.0) -> th.FloatOrArr:
        r"""Spectral shape function $C(s)$.

        $$C(s) = s^3 \left( \frac{7}{4 + 3 s^2} \right)^\frac{7}{2}
        = \text{norm} f_p^3 \left( \frac{7}{4 + 3 s^2} \right)^\frac{7}{2}$$
        This function is a fit to the sound wave power spectrum from simulations.
        :hindmarsh_2017:`\ ` eq. 36
        :caprini_2020:`\ ` eq. 30

        :param s: Relative frequency $s$ with respect to the peak frequency
        :param norm: Normalization factor
        :return: Spectral shape function $C(s)$
        """
        return norm * s**3 * (7 / (4 + 3 * s ** 2))**(7 / 2)

    def f_turb(self):
        r"""Calculate peak frequency for turbulence.

        $$f_\text{turb} = 2.7 \cdot 10^{-5} \text{Hz} \frac{1}{v_\text{wall}}
        \frac{\beta}{H_*} \frac{T_*}{100 \text{GeV}}
        \left( \frac{g_*}{100} \right)^{1/6}$$
        :caprini_2015:`\ ` eq. 18
        """
        if self.v_wall is None:
            raise ValueError("v_wall is required for computing the peak frequency for turbulence.")
        return 27e-6 * (1 / self.v_wall) * self.beta_over_H * (self.T_star / 100) * (self.g_star / 100)**(1/6)

    def power_spectrum(self, f: th.FloatArr1D, log_errors: bool = False) -> th.FloatArr1D:  # noqa: ARG002
        """Power spectrum from sound waves (conservative)."""
        return tp.cast("th.FloatArr1D", self.power_spectrum_sw_conservative(f))

    def power_spectrum_full(self, f: th.FloatOrArr) -> th.FloatOrArr:
        """Total power spectrum from sound waves and turbulence."""
        return self.power_spectrum_sw(f) + self.power_spectrum_turb(f)

    def power_spectrum_full_conservative(self, f: th.FloatOrArr) -> th.FloatOrArr:
        """Total power spectrum from sound waves (conservative) and turbulence."""
        return self.power_spectrum_sw_conservative(f) + self.power_spectrum_turb(f)

    def power_spectrum_sw(
            self,
            f: th.FloatOrArr,
            omega_tilde_gw: float = const.DEFAULT_OMEGA_TILDE_GW) -> th.FloatOrArr:
        r"""Power spectrum from sound waves.

        $$h^2 \frac{d \Omega_{\text{gw},0}}{d \ln f}
        = h^2 \cdot 2.061 F_{\text{gw},0} \Gamma^2 \bar{U}_f^4 (H_n R_*) \tilde{\Omega}_\text{gw} C(\frac{f}{f_p,0})$$
        :hindmarsh_2017:`\ ` eq. 45
        :hindmarsh_2017_erratum:`\ ` eq. 2

        Please note that the original version of :hindmarsh_2017:`\ ` eq. 45 is missing a factor of 3.

        $F_{\text{gw},0}$ depends on the value of $h$,
        which is why the result is multiplied by $h^2$ to get a quantity that is independent of $h$.

        The numerical prefactor comes from
        $$0.68 \cdot 3.57e-5 \cdot (8*pi)^(1/3) \cdot 0.12
        = 8.5e-6
        = 0.68 \cdot F_{\text{gw},0} \cdot \text{geometric} \cdot \tilde{\Omega}_\text{gw}$$

        :param f: Frequency $f$
        :param omega_tilde_gw: $\tilde{\Omega}_\text{gw}$
        """
        return self.power_spectrum_common(omega_tilde_gw=omega_tilde_gw) \
            * 0.687 * self.r_star * self.C(s=self.s(f))

    def power_spectrum_sw_conservative(self, f: th.FloatOrArr) -> th.FloatOrArr:
        """Calculate power spectrum from sound waves (conservative).

        For the conservative estimate, take the shock time no larger than 1.
        """
        return min(self.H_tsh, 1.) * self.power_spectrum_sw(f)

    def power_spectrum_turb(self, f: th.FloatOrArr) -> th.FloatOrArr:
        r"""Calculate power spectrum from turbulence for a given frequency f.

        :caprini_2015:`\ ` eq. 16
        """
        fp = f / self.f_turb()
        return 3.35e-4 / self.beta_over_H \
            * (self.k_turb * self.alpha / (1 + self.alpha))**(3/2) \
            * (100 / self.g_star)**(1/3) * self.v_wall * self.S_turb(f, fp)

    def S_turb(self, f: th.FloatOrArr, fp: float) -> th.FloatOrArr:
        r"""Calculate the spectral shape from turbulence.

        :caprini_2015:`\ ` eq. 17
        """
        return fp**3 / ((1 + fp)**(11/3) * (1 + 8 * math.pi * f / self.h_star()))
