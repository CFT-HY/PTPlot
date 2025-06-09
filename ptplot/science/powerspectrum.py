"""Ansätze for calculating the SGWB power spectra

This file contains the ansätze needed to calculate the power spectrum from
sound waves and from turbulence (although the latter is not used).
Unless stated otherwise, the equations here follow those in M. Hindmarsh et al.
Phys.Rev.D 96 (2017) 10, 103520, Phys.Rev.D 101 (2020) 8, 089902 (erratum)
(1704.05871).

Contains the following functions:
    * rstar_to_beta - converts from rstar to beta
    * beta_to_rstar - converts from beta to rstar
    * get_SNR_value - calculates the SNR for a specific power spectrum
And the following class:
    * PowerSpectrum - contains the quantities and functions to obtain a power spectrum
"""

import math
import typing as tp

import numpy as np

from ptplot.science import const
from ptplot.science.espinosa import ubarf
from ptplot.science.snr import StockBkg_ComputeSNR


def rstar_to_beta(rstar: float, vw: float, cs: float = const.CS0) -> float:
    r"""Convert R_* to \Beta_* for a given wall velocity

    Parameters
    ----------
    rstar : float
        Mean bubble separation
    vw : float
        Wall velocity
    cs : float
        Speed of sound (default to 1/sqrt(3))

    Returns
    -------
    beta : float
        Inverse phase transition duration
    """
    return math.pow(8.0 * math.pi, 1.0/3.0) * max(vw, cs) / rstar


def beta_to_rstar(beta: float, vw: float, cs: float = const.CS0) -> float:
    r"""Convert \Beta_* to R_* for a given wall velocity

    Parameters
    ----------
    beta : float
        Inverse phase transition duration
    vw : float
        Wall velocity
    cs : float
        Speed of sound (default to 1/sqrt(3))

    Returns
    -------
    rstar : float
        Mean bubble separation
    """
    return math.pow(8.0 * math.pi, 1.0/3.0) * max(vw,cs) / beta


def get_SNR_value(
        fSens: np.ndarray,
        omSens: np.ndarray,
        duration: float,
        Tstar: float = const.DEFAULT_T_STAR,
        gstar: float = const.DEFAULT_G_STAR,
        vw: float = const.DEFAULT_VW,
        alpha: float = const.DEFAULT_ALPHA,
        BetaoverH: float = const.DEFAULT_BETA_OVER_H) -> np.ndarray:
    """Calculate the SNR value for a given power spectrum

    Note that this function is currently not being used by the code, but it
    is included here for legacy reasons.

    Parameters
    ----------
    fSens : np.ndarray
        List of frequencies in Hz corresponding to omSens
    omSens : np.ndarray
        List of sensitivities in Omega units
    duration : float
        Observation time in seconds
    Tstar : float, Optional
        Transition temperature (default to 180.0)
    gstar : float, Optional
        Degrees of freedom (default to 100)
    vw : float, Optional
        Wall velocity (default to 0.9)
    alpha : float, Optional
        Phase transition strength (default to 0.1)
    BetaoverH : float, Optional
        Inverse phase transition duration relative to H (default to 10)

    Returns
    -------
    snr : np.ndarray
        Signal-to-noise ratio
    """
    ps = PowerSpectrum(
        T_star=Tstar, g_star=gstar,
        vw=vw, alpha=alpha, beta_over_H=BetaoverH
    )
    snr_value, frange = StockBkg_ComputeSNR(
        fSens,
        omSens,
        fSens,
        ps.power_spectrum_sw_conservative(fSens),
        duration,
        1.e-6,
        1
    )
    return snr_value


class PowerSpectrum:
    """A class used to define the power spectrum

    Attributes
    ----------
    beta_over_H : float
        Inverse phase transition duration relative to H
    T_star : float
        Transition temperature (default to 180.0)
    g_star : float
        Degrees of freedom (default to 100)
    vw : float
        Wall velocity
    adiabatic_ratio : float
        Adiabatic index (Gamma) (default to 4.0/3.0)
    zp : float
        Peak angular frequency in units of the mean bubble separation (default to 10)
    alpha : float, Optional
        Phase transition strength
    k_turb : float
         Fraction of latent heat that is transformed into magnetohydrodynamic turbulence (default 1.97/65.0)
    H_rstar : float
        Typical bubble radius
    ubarf : float
        rms fluid velocity
    h_star : float
        Reduced Hubble rate, needed for turbulence
    H_tsh : float
        Shock time
    """
    def __init__(
            self,
            beta_over_H: float = None,
            T_star: float = const.DEFAULT_T_STAR,
            g_star: float = const.DEFAULT_G_STAR,
            vw: float = None,
            adiabatic_ratio: float = const.DEFAULT_ADIABATIC_RATIO,
            zp: float = 10,
            alpha: tp.Optional[float] = None,
            k_turb: float = 1.97 / 65.0,
            H_rstar: float = None,
            ubarf_in: float = None):
        """
        Parameters
        ----------
        beta_over_H : float
            Inverse phase transition duration relative to H
        T_star : float
            Transition temperature (default to 180.0)
        g_star : float
            Degrees of freedom (default to 100)
        vw : float
            Wall velocity
        adiabatic_ratio : float
            Adiabatic index (Gamma) (default to 4.0/3.0)
        zp : float
            Peak angular frequency in units of the mean bubble separation (default to 10)
        alpha : float, Optional
            Phase transition strength
        k_turb : float
            Fraction of latent heat that is transformed into magnetohydrodynamic turbulence (default 1.97/65.0) (default 1.97/65.0)
        H_rstar : float
            Typical bubble radius
        ubarf_in : float
            Input value of the rms fluid velocity
        """
        self.beta_over_H: float = beta_over_H
        self.T_star: float = T_star
        self.g_star: float = g_star
        self.vw: float = vw
        self.adiabatic_ratio: float = adiabatic_ratio
        self.zp: float = zp
        self.alpha: float = alpha
        self.k_turb: float = k_turb

        self.h_star: float = 16.5e-6 * (self.T_star / 100.0) * np.power(self.g_star / 100.0, 1.0 / 6.0)

        # Either take ubarf_in as-is, or calculate ubarf from the wall velocity
        if (vw is not None) and (ubarf_in is None):
            self.ubarf = ubarf(vw, alpha, adiabatic_ratio)
        elif (vw is None) and (ubarf_in is not None):
            self.ubarf = ubarf_in
        else:
            raise ValueError("Either ubarf_in or vw must be set, but not both")

        # Calculate typical bubble radius
        if (H_rstar is None) and (beta_over_H is not None):
            self.H_rstar = beta_to_rstar(self.beta_over_H, self.vw)
        elif (H_rstar is not None) and (beta_over_H is None):
            self.H_rstar = H_rstar
        else:
            raise ValueError("Either H_rstar or BetaoverH must be set, but not both")

        # Compute shock time
        self.H_tsh: float = self.H_rstar / self.ubarf

    # This function does not depend on the power spectrum itself, and so does
    # not inherit the class instance information (no self in arguments).
    # Note that this function used to be called Ssw, but it was renamed in 2023
    # to match the notation used in equation 36 of 1704.05871.
    # Function C(f)
    @staticmethod
    def Csw(fp, norm=1.0):
        """Calculate spectral shape for gw from sound waves

        For a given peak frequency, calculate spectral shape of a single broken
        power law fit to simulation results for gw from sound waves.
        """
        return norm*np.power(fp, 3.0) * np.power(7.0/(4.0 + 3.0 * np.power(fp, 2.0)), 7.0/2.0)

    def get_shock_time(self) -> float:
        """Calculate shock time"""
        return self.H_tsh

    def fsw(self) -> float:
        """Calculate true peak frequency

        This follows equation 43 in 1704.05871. Note that the numerical prefactor
        is absorbed in the definition of beta_to_rstar() above;
        (1/(H_n*R_*)) = 1/((8*pi)^{1/3}*vw/BetaoverH) .
        """
        return 26.0e-6 * (1.0/self.H_rstar) * (self.zp/10.0) \
            * (self.T_star/100) * np.power(self.g_star/100, 1.0/6.0)

    # This follows equations 39 - 45 in 1704.05871 (and the paper erratum)
    def power_spectrum_sw(self, f):
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
        return const.H_PLANCK**2 * 3.0 \
            * 0.687 * 3.57e-5 * 0.012 * np.power(100.0 / self.g_star, 1.0/3.0) \
            * self.adiabatic_ratio * self.adiabatic_ratio \
            * np.power(self.ubarf, 4.0) * self.H_rstar * self.Csw(fp)

    # The following three functions (*turb) are taken from 1512.06239.
    # However, in later papers the contribution from turbulence is neglected,
    # as further studies to understand turbulence are needed. As such, these
    # three functions are not called anywhere in the code by default.
    # However, these can still be turned on by overriding the sw_only flag.
    def fturb(self):
        """Calculate peak frequency for turbulence

        This function follows equation 18 equation of 1512.06239.
        """
        return 27e-6 * (1.0/self.vw) * self.beta_over_H * (self.T_star/100.0) * np.power(self.g_star/100, 1.0/6.0)

    def Sturb(self, f, fp):
        """Calculate the spectral shape from turbulence

        This function follows equation 17 equation of 1512.06239.
        """
        return np.power(fp,3.0) / (np.power(1 + fp, 11.0/3.0) * (1 + 8 * math.pi * f / self.h_star))

    def power_spectrum_turb(self, f):
        """Calculate power spectrum from turbulence for a given frequency f

        This function follows equation 16 equation of 1512.06239.
        """
        fp = f/self.fturb()
        return 3.35e-4 / self.beta_over_H \
            * np.power(self.k_turb * self.alpha / (1 + self.alpha), 3.0/2.0) \
            * np.power(100/self.g_star, 1.0/3.0) * self.vw * self.Sturb(f, fp)

    def power_spectrum_sw_conservative(self, f):
        """Calculate power spectrum from sound waves (conservative)

        For the conservative estimate, take the shock time no larger than 1.
        """
        return min(self.H_tsh, 1.0) * self.power_spectrum_sw(f)
    
    def power_spectrum(self, f):
        """Calculate total power spectrum from sound waves and turbulence"""
        return self.power_spectrum_sw(f) + self.power_spectrum_turb(f)

    def power_spectrum_conservative(self, f):
        """Calculate total power spectrum from sound waves (conservative) and turbulence"""
        return self.power_spectrum_sw_conservative(f) + self.power_spectrum_turb(f)
