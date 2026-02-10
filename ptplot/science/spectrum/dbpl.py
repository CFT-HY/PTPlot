"""Double broken power law (DBPL) power spectrum"""

import numpy as np

from ptplot.science import const
from ptplot.science.engine import ENGINE_NAMES, Engine
from ptplot.science.spectrum.base import PowerSpectrum
import ptplot.science.type_hints as th


class PowerSpectrumDBPL(PowerSpectrum):
    """
    Double broken power law (DBPL) power spectrum

    Based on
    https://version.helsinki.fi/hakkijen/ptplot-with-pttools
    """
    ENGINE: Engine = Engine.DBPL
    NAME: str = ENGINE_NAMES[ENGINE]
    SHORT_NAME: str = ENGINE.name

    def __init__(
            self,
            beta_over_H: float | None = None,
            T_star: float = const.DEFAULT_T_STAR,
            g_star: float = const.DEFAULT_G_STAR,
            vw: float | None = None,
            adiabatic_ratio: float = const.DEFAULT_ADIABATIC_RATIO,
            zp: float = const.DEFAULT_ZP,
            alpha: float | None = None,
            k_turb: float = const.DEFAULT_K_TURB,
            r_star: float | None = None,
            ubarf_in: float | None = None,
            zb: float = 1.):
        super().__init__(
            beta_over_H=beta_over_H, T_star=T_star, vw=vw, alpha=alpha,
            r_star=r_star, g_star=g_star, adiabatic_ratio=adiabatic_ratio, ubarf_in=ubarf_in, zp=zp
        )
        self.zb: float = zb

        # Compute ratio of the two breaks in the spectrum
        self.rb: float = self.zb / self.zp

    def mu(self) -> float:
        """Calculate prefactor for the peak power of the gw power spectrum

        This is an approximate form of the function based on equations 5.8. and 5.9 in 1909.10040.
        It defines the peak power A of the spectrum as
        mu(rb)*A = 3*(adiabaticRatio*Ubarf**2**2*Omegatilde.
        We take Omegatilde=0.012 when calculating the power spectrum.
        """
        return 4.78 - 6.27 * self.rb + 3.34 * np.power(self.rb, 2.0)

    def Msw(self, s, b: float = 1.0) -> float:
        """Calculate spectral shape for gw from sound waves

        For a given peak frecuency, calculate spectral shape of a double broken power law fit to the Sound Shell Model power spectrum.

        This follows equation 2.16 in 2106.05984, with the value b = 1 defining the spectral slope
        between the two breaks in the spectrum, as in 1909.10040.
        """
        m = (9.0 * np.power(self.rb, 4.0) + b) / (np.power(self.rb, 4.0) + 1)

        return \
            np.power(s, 9.0) * np.power((1.0 + np.power(self.rb, 4.0)) / (np.power(self.rb, 4.0) + np.power(s, 4.0)),
            (9.0 - b) / 4.0) * np.power((b + 4.0) / (b + 4.0 - m + m * np.power(s, 2.0)),
            (b + 4.0) / 2.0)

    @property
    def fsw(self) -> float:
        """Calculate true peak frequency

        This follows equation 43 in 1704.05871. Note that the numerical prefactor
        is absorbed in the definition of beta_to_rstar() above;
        (1/(H_n*R_*)) = 1/((8*pi)^{1/3}*vw/BetaoverH) .
        """
        return 26.0e-6 * (1.0 / self.r_star) * (self.zp / 10.0) \
            * (self.T_star/100) * np.power(self.g_star/100, 1.0/6.0)

    def J(self) -> float:
        """Calculate the source lifetime

        This follows equation 2.8 in 2106.05984.
        """

        # K_frac is the kinetic energy fraction in the fluid, given by
        # K_frac = adiabaticRatio*Ubarf**2 (eq 22 in 1910.13125).
        K_frac = self.adiabatic_ratio * np.power(self.ubarf, 2.0)

        return self.r_star * (1.0 - 1.0 / (np.sqrt(1.0 + 2.0 * self.r_star / np.sqrt(K_frac))))

    def power_spectrum(self, f: th.FloatOrArr) -> th.FloatOrArr:
        """Calculate power spectrum from sound waves for a given frequency f using the double broken power-law ansatz

        This follows equations 2.15 and 2.16 in 2106.05984 and 5.6 - 5.8 in 1909.10040.
        """

        # See fsw() method, and definition of beta_to_rstar().
        s = f / self.fsw

        # Some of the equations below were derived assuming this value for h,
        # we add it here to remove the h dependence from the final results.
        # h_planck = 0.678

        # Fgw0 is 3.57e-5*(100/gstar)^(1/3), and implicitly includes
        # Omega_photons. The implicit Hubble constant dependence of equation
        # 45 (erratum equation 2) comes from Omega_photons. Multiplying both
        # sides by h_planck removes that, and so the result does not depend
        # on a particular measurement of the Hubble constant.

        # Thus, this returns h^2 OmGW, which does not depend on a
        # particular value of the Hubble constant.
        return const.H_PLANCK2 * 3.0 * 3.57e-5 * 0.012 * np.power(100.0/self.g_star, 1.0/3.0) \
            * self.adiabatic_ratio * self.adiabatic_ratio * np.power(self.ubarf, 4.0) / self.mu() \
            * self.J() * self.Msw(s)
