"""Broken power law (BPL) power spectrum"""

import math

import numpy as np
from pandas import DataFrame

from ptplot.science import const
from ptplot.science.mission_profile import DEFAULT_MISSION_PROFILE, MissionProfile
from ptplot.science.spectrum.base import PowerSpectrum
import ptplot.science.type_hints as th


class PowerSpectrumBPL(PowerSpectrum):
    r"""Broken power law (BPL) power spectrum

    Based on :hindmarsh_2017:`\ ` and `hindmarsh_2017_erratum:`\ `.

    Also contains functions for turbulence.
    However, in later papers the contribution from turbulence is neglected,
    as further studies to understand turbulence are needed.
    As such, the turbulence functions are not called anywhere in the code by default.
    However, they can still be turned on by overriding the sw_only flag.
    """
    def csv(
            self,
            path: str | None = None,
            mission_profile: MissionProfile = DEFAULT_MISSION_PROFILE,
            sw_only: bool = True) -> str | None:
        r"""Export the power spectrum as CSV

        :param path: A path in which to save the data
        :param mission_profile: Which sensitivity curve to use
        :param sw_only: Whether to ignore turbulence
        :return: If a path is not given, the data will be returned as a string.
        """
        if sw_only:
            return super().csv(path=path, mission_profile=mission_profile)
        f = mission_profile.f
        df = DataFrame({
            "f": f,
            "omegaSens": mission_profile.sensitivity,
            "omegaSW": self.power_spectrum(f),
            "omegaTurb": self.power_spectrum_turb(f),
            "omegaTot": self.power_spectrum_full_conservative(f)
        })
        return df.to_csv(path)

    @staticmethod
    def Csw(fp: th.FloatOrArr, norm: float = 1.0) -> th.FloatOrArr:
        r"""Calculate spectral shape for gw from sound waves

        For a given peak frequency, calculate spectral shape of a single broken
        power law fit to simulation results for gw from sound waves.
        :hindmarsh_2017:`\ ` eq. 36

        This function was previously known as $S_{sw}$,
        but was renamed in 2023 to match the notation in the article.
        """
        return norm * np.power(fp, 3.0) * np.power(7.0 / (4.0 + 3.0 * np.power(fp, 2.0)), 7.0 / 2.0)

    def fsw(self) -> float:
        r"""True peak frequency

        :hindmarsh_2017:`\ ` eq. 43

        Note that the numerical prefactor
        is absorbed in the definition of beta_to_rstar() above;
        (1/(H_n*R_*)) = 1/((8*pi)^{1/3}*vw/BetaoverH) .
        """
        return 26.0e-6 * (1.0 / self.r_star) * (self.zp / 10.0) \
            * (self.T_star / 100) * np.power(self.g_star / 100, 1.0 / 6.0)

    # This follows equations 39 - 45 in 1704.05871 (and the paper erratum)
    def power_spectrum_sw(self, f: th.FloatOrArr) -> th.FloatOrArr:
        r"""Power spectrum from sound waves for a given frequency f

        :hindmarsh_2017:`\ ` eq. 45
        :hindmarsh_2017_erratum:`\ ` eq. 2
        """

        # This is based on equation 45 in 1704.05871, with the numerical
        # prefactor coming from 0.68*(3.57e-5)*(8*pi)^(1/3)*0.12 = 8.5e-6
        # (=0.68*Fgw0*geometric*Omtil)
        #
        # Using equation R_* = (8*pi)^{1/3}*vw/beta (section VI, same paper),
        # thus: H_n*R_* = (8*pi)^{1/3}*vw/BetaoverH
        #
        # See fsw() method, and definition of beta_to_rstar()
        fp = f / self.fsw()

        # Some of the equations below were derived assuming this value for h,
        # we add it here to remove the h dependence from the final results
        # h_planck = 0.678

        # Equations 39 and 45 in 1704.05871 are missing the factor of 3 [typo];
        # and there is no h_planck in eq 45 (it is implicit in the RHS).
        # Note also typo below eq 45, 0.12 -> 0.012 for OmTilde.
        #
        # The resulting 3*0.687 = 2.061 prefactor is also explained in equation
        # 2 of the erratum.
        #
        # Fgw0 is 3.57e-5*(100/hstar)^(1/3), and implicitly includes
        # Omega_photons. The implicit Hubble constant dependence of equation
        # 45 (erratum equation 2) comes from Omega_photons. Multiplying both
        # sides by h_planck removes that, and so the result does not depend
        # on a particular measurement of the Hubble constant.
        #
        # Thus, this returns h^2 OmGW, which does not depend on a
        # particular value of the Hubble constant.
        return const.H_PLANCK ** 2 * 3.0 \
            * 0.687 * 3.57e-5 * 0.012 * np.power(100.0 / self.g_star, 1.0 / 3.0) \
            * self.adiabatic_ratio * self.adiabatic_ratio \
            * np.power(self.ubarf, 4.0) * self.r_star * self.Csw(fp)

    def fturb(self):
        r"""Calculate peak frequency for turbulence

        :caprini_2015:`\ ` eq. 18
        """
        return 27e-6 * (1.0 / self.vw) * self.beta_over_H * (self.T_star / 100.0) * np.power(self.g_star / 100,
                                                                                             1.0 / 6.0)

    def Sturb(self, f: th.FloatOrArr, fp: float) -> th.FloatOrArr:
        r"""Calculate the spectral shape from turbulence

        :caprini_2015:`\ ` eq. 17
        """
        return np.power(fp, 3.0) / (np.power(1 + fp, 11.0 / 3.0) * (1 + 8 * math.pi * f / self.h_star))

    def power_spectrum_turb(self, f: th.FloatOrArr) -> th.FloatOrArr:
        r"""Calculate power spectrum from turbulence for a given frequency f

        :caprini_2015:`\ ` eq. 16
        """
        fp = f / self.fturb()
        return 3.35e-4 / self.beta_over_H \
            * np.power(self.k_turb * self.alpha / (1 + self.alpha), 3.0 / 2.0) \
            * np.power(100 / self.g_star, 1.0 / 3.0) * self.vw * self.Sturb(f, fp)

    def power_spectrum_sw_conservative(self, f: th.FloatOrArr) -> th.FloatOrArr:
        """Calculate power spectrum from sound waves (conservative)

        For the conservative estimate, take the shock time no larger than 1.
        """
        return min(self.H_tsh, 1.0) * self.power_spectrum_sw(f)

    def power_spectrum(self, f: th.FloatOrArr) -> th.FloatOrArr:
        """Power spectrum from sound waves (conservative)"""
        return self.power_spectrum_sw_conservative(f)

    def power_spectrum_full(self, f: th.FloatOrArr) -> th.FloatOrArr:
        """Total power spectrum from sound waves and turbulence"""
        return self.power_spectrum_sw(f) + self.power_spectrum_turb(f)

    def power_spectrum_full_conservative(self, f: th.FloatOrArr) -> th.FloatOrArr:
        """Total power spectrum from sound waves (conservative) and turbulence"""
        return self.power_spectrum_sw_conservative(f) + self.power_spectrum_turb(f)
