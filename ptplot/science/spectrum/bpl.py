"""
Broken power law (BPL) power spectrum

This file contains the ansätze needed to calculate the power spectrum from
sound waves and from turbulence (although the latter is not used).
Unless stated otherwise, the equations here follow those in M. Hindmarsh et al.
Phys.Rev.D 96 (2017) 10, 103520, Phys.Rev.D 101 (2020) 8, 089902 (erratum)
(1704.05871).
"""

import math

import numpy as np

from ptplot.science import const
from ptplot.science.spectrum.base import PowerSpectrum
import ptplot.science.type_hints as th


class PowerSpectrumBPL(PowerSpectrum):
    """Broken power law (BPL) power spectrum"""

    # This function does not depend on the power spectrum itself, and so does
    # not inherit the class instance information (no self in arguments).
    # Note that this function used to be called Ssw, but it was renamed in 2023
    # to match the notation used in equation 36 of 1704.05871.
    # Function C(f)
    @staticmethod
    def Csw(fp: th.FloatOrArr, norm: float = 1.0) -> th.FloatOrArr:
        """Calculate spectral shape for gw from sound waves

        For a given peak frequency, calculate spectral shape of a single broken
        power law fit to simulation results for gw from sound waves.
        """
        return norm * np.power(fp, 3.0) * np.power(7.0 / (4.0 + 3.0 * np.power(fp, 2.0)), 7.0 / 2.0)

    def fsw(self) -> float:
        """Calculate true peak frequency

        This follows equation 43 in 1704.05871. Note that the numerical prefactor
        is absorbed in the definition of beta_to_rstar() above;
        (1/(H_n*R_*)) = 1/((8*pi)^{1/3}*vw/BetaoverH) .
        """
        return 26.0e-6 * (1.0 / self.r_star) * (self.zp / 10.0) \
            * (self.T_star / 100) * np.power(self.g_star / 100, 1.0 / 6.0)

    # This follows equations 39 - 45 in 1704.05871 (and the paper erratum)
    def power_spectrum_sw(self, f: th.FloatOrArr) -> th.FloatOrArr:
        """Calculate power spectrum from sound waves for a given frequency f

        This function follows equation 45 (erratum equation 2) of 1704.05871.
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

    # The following three functions (*turb) are taken from 1512.06239.
    # However, in later papers the contribution from turbulence is neglected,
    # as further studies to understand turbulence are needed. As such, these
    # three functions are not called anywhere in the code by default.
    # However, these can still be turned on by overriding the sw_only flag.
    def fturb(self):
        """Calculate peak frequency for turbulence

        This function follows equation 18 equation of 1512.06239.
        """
        return 27e-6 * (1.0 / self.vw) * self.beta_over_H * (self.T_star / 100.0) * np.power(self.g_star / 100,
                                                                                             1.0 / 6.0)

    def Sturb(self, f: th.FloatOrArr, fp: float) -> th.FloatOrArr:
        """Calculate the spectral shape from turbulence

        This function follows equation 17 equation of 1512.06239.
        """
        return np.power(fp, 3.0) / (np.power(1 + fp, 11.0 / 3.0) * (1 + 8 * math.pi * f / self.h_star))

    def power_spectrum_turb(self, f: th.FloatOrArr) -> th.FloatOrArr:
        """Calculate power spectrum from turbulence for a given frequency f

        This function follows equation 16 equation of 1512.06239.
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
        """Calculate total power spectrum from sound waves and turbulence"""
        return self.power_spectrum_sw(f)  # + self.power_spectrum_turb(f)

    def power_spectrum_conservative(self, f: th.FloatOrArr) -> th.FloatOrArr:
        """Calculate total power spectrum from sound waves (conservative) and turbulence"""
        return self.power_spectrum_sw_conservative(f) + self.power_spectrum_turb(f)
