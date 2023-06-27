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


import numpy as np
import math
import sys

try:
    from .espinosa import ubarf
    from .snr import *
except ValueError:
    from espinosa import ubarf
    from snr import *
except ImportError:
    from espinosa import ubarf
    from snr import *

def rstar_to_beta(rstar, vw):
    """Convert R_* to \Beta_* for a given wall velocity

    Parameters
    ----------
    rstar : float
        Mean bubble separation
    vw : float
        Wall velocity

    Returns
    -------
    beta : float
        Nucleation rate
    """

    return math.pow(8.0*math.pi,1.0/3.0)*vw/rstar

def beta_to_rstar(beta, vw):
    """Convert \Beta_* to R_* for a given wall velocity

    Parameters
    ----------
    beta : float
        Nucleation rate
    vw : float
        Wall velocity

    Returns
    -------
    beta : float
        Mean bubble separation
    """

    return math.pow(8.0*math.pi,1.0/3.0)*vw/beta

def get_SNR_value(fSens, omSens, duration,
                  Tstar=180.0, gstar=100, vw=0.9, alpha=0.1, BetaoverH=10):
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
        Inverse phase transition duration (default to 10)

    Returns
    -------
    snr : tuple[float, np.ndarray]
        Signal-to-noise ratio
    """

    ps = PowerSpectrum(Tstar=Tstar, gstar=gstar,
                       vw=vw, alpha=alpha, BetaoverH=BetaoverH)

    snr, frange = StockBkg_ComputeSNR(fSens,
                                      omSens,
                                      fSens,
                                      ps.power_spectrum_sw_conservative(fSens),
                                      duration,
                                      1.e-6,
                                      1)

    return snr
    
class PowerSpectrum:
    """A class used to define the power spectrum

    Attributes
    ----------
    BetaoverH : float
        Inverse phase transition duration
    Tstar : float
        Transition temperature (default to 180.0)
    gstar : float
        Degrees of freedom (default to 100)
    vw : float
        Wall velocity
    adiabaticRatio : float
        Adiabatic index (Gamma) (default to 4.0/3.0)
    zp : float
        Peak angular frequency in units of the mean bubble separation (default to 10)
    alpha : float, Optional
        Phase transition strength
    kturb : float
         Fraction of latent heat that is transformed into magnetohydrodynamic turbulence (default 1.97/65.0)
    H_rstar : float
        Typical bubble radius
    ubarf_in : float
        Input value of the rms fluid velocity
    hstar : float
        Reduced Hubble rate, needed for turbulence
    H_tsh : float
        Shock time
    """

    def __init__(self,
                 BetaoverH = None,
                 Tstar = 180.0,
                 gstar = 100,
                 vw = None,
                 adiabaticRatio = 4.0/3.0,
                 zp = 10,
                 alpha = None,
                 kturb = 1.97/65.0,
                 H_rstar = None,
                 ubarf_in = None):
        """
        Parameters
        ----------
        BetaoverH : float
            Inverse phase transition duration
        Tstar : float
            Transition temperature (default to 180.0)
        gstar : float
            Degrees of freedom (default to 100)
        vw : float
            Wall velocity
        adiabaticRatio : float
            Adiabatic index (Gamma) (default to 4.0/3.0)
        zp : float
            Peak angular frequency in units of the mean bubble separation (default to 10)
        alpha : float, Optional
            Phase transition strength
        kturb : float
            Fraction of latent heat that is transformed into magnetohydrodynamic turbulence (default 1.97/65.0) (default 1.97/65.0)
        H_rstar : float
            Typical bubble radius
        ubarf_in : float
            Input value of the rms fluid velocity
        """

        self.BetaoverH=BetaoverH
        self.Tstar = Tstar
        self.gstar = gstar
        self.vw = vw
        self.adiabaticRatio = adiabaticRatio
        self.zp = zp
        self.alpha = alpha
        self.kturb = kturb

        self.hstar = 16.5e-6*(self.Tstar/100.0) \
                     *np.power(self.gstar/100.0,1.0/6.0)

        # Either take ubarf_in as-is, or calculate ubarf from the wall velocity
        if (vw is not None) and (ubarf_in is None):
            self.ubarf = ubarf(vw, alpha)
        elif (vw is None) and (ubarf_in is not None):
            self.ubarf = ubarf_in
        else:
            raise ValueError("Either ubarf_in or vw must be set, but not both")

        # Calculate typical bubble radius
        if (H_rstar is None) and (BetaoverH is not None):
            self.H_rstar = beta_to_rstar(self.BetaoverH, self.vw)
        elif (H_rstar is not None) and (BetaoverH is None):
            self.H_rstar = H_rstar
        else:
            raise ValueError("Either H_rstar or BetaoverH must be set, but not both")

        # Compute shock time
        self.H_tsh = self.H_rstar/self.ubarf

    # This function does not depend on the power spectrum itself, and so does
    # not inherit the class instance information (no self in arguments).
    # Note that this function used to be called Ssw, but it was renamed in 2023
    # to match the notation used in equation 36 of 1704.05871.
    # Function C(f) (TODO: rename it to Csw)
    @staticmethod
    def Ssw(fp, norm=1.0):
        """Calculate spectral shape for gw from sound waves

        For a given peak frequency, calculate spectral shape of a single broken
        power law fit to simulation results for gw from sound waves.
        """

        return norm*np.power(fp,3.0) \
            *np.power(7.0/(4.0 + 3.0*np.power(fp,2.0)),7.0/2.0)

    def get_shocktime(self):
        """Calculate shock time
        """

        return self.H_tsh
    
    # This follows equation 43 in 1704.05871. Note that the numerical prefactor
    # is absorbed in the definition of beta_to_rstar() above;
    # (1/(H_n*R_*)) = 1/((8*pi)^{1/3}*vw/BetaoverH) .
    def fsw(self):
        """Calculate true peak frequency
        """

        return (26.0e-6)*(1.0/self.H_rstar)*(self.zp/10.0) \
            *(self.Tstar/100)*np.power(self.gstar/100,1.0/6.0)        

    # This follows equations 39 - 45 in 1704.05871 (and the paper erratum)
    def power_spectrum_sw(self, f):
        """Calculate power spectrum from sound waves for a given frequency f

        This function follows equation 45 equation (erratum equation 2) of
        1704.05871.
        """

        # This is based on equation 45 in 1704.05871, with the numerical
        # prefactor coming from 0.68*(3.57e-5)*(8*pi)^(1/3)*0.12 = 8.5e-6
        # (=0.68*Fgw0*geometric*Omtil)
        #
        # Using equation R_* = (8*pi)^{1/3}*vw/beta (section IV, same paper),
        # thus: H_n*R_* = (8*pi)^{1/3}*vw/BetaoverH
        #
        # See fsw() method, and definition of beta_to_rstar()
        fp = f/self.fsw(f)

        h_planck = 0.678

        # Equations 39 and 45 in 1704.05871 are missing the factor of 3 [typo];
        # and there is no h_planck in eq 45 (it is implicit in the RHS).
        # Note also typo below eq 45, 0.12 -> 0.012 for OmTilde.
        #
        # The resulting 3*0.687 prefactor is also explained in equation 2 of
        # the erratum.
        #
        # Fgw0 is 3.57e-5*(100/hstar)^(1/3), and implicitly includes
        # Omega_photons. The implicit Hubble constant dependence of equation
        # 45 (erratum equation 2) comes from Omega_photons. Multiplying both
        # sides by h_planck removes that, and so the result does not depend
        # on a particular measurement of the Hubble constant.
        #
        # Thus, this returns h^2 OmGW, which does not depend on a
        # particular value of the Hubble constant.
        return h_planck*h_planck*3.0 \
            *0.687*3.57e-5*0.012*np.power(100.0/self.gstar,1.0/3.0) \
            *self.adiabaticRatio*self.adiabaticRatio \
            *np.power(self.ubarf,4.0)*self.H_rstar*self.Ssw(fp)    

    # The following three functions (*turb) are taken from 1512.06239.
    # However, in later papers the contribution from turbulence is neglected,
    # as further studies to understand turbulence are needed. As such, these
    # three functions are not called anywhere in the code by default.
    # However, these can still be turned on by overriding the sw_only flag.
    def fturb(self):
        """Calculate peak frequency for turbulence

        This function follows equation 18 equation of 1512.06239.
        """

        return (27e-6)*(1.0/self.vw)*(self.BetaoverH)*(self.Tstar/100.0) \
            *np.power(self.gstar/100,1.0/6.0)

    def Sturb(self, f, fp):
        """Calculate the spectral shape from turbulence

        This function follows equation 17 equation of 1512.06239.
        """

        return np.power(fp,3.0)/(np.power(1 + fp, 11.0/3.0) \
                                 *(1 + 8*math.pi*f/self.hstar))

    def power_spectrum_turb(self, f):
        """Calculate power spectrum from turbulence for a given frequency f

        This function follows equation 16 equation of 1512.06239.
        """

        fp = f/self.fturb
        return (3.35e-4)/self.BetaoverH \
            *np.power(self.kturb*self.alpha/(1 + self.alpha),3.0/2.0) \
            *np.power(100/self.gstar,1.0/3.0)*self.vw*self.Sturb(f,fp)

    def power_spectrum_sw_conservative(self, f):
        """Calculate power spectrum from sound waves (conservative)

        For the conservative estimate, take the shock time no larger than 1.
        """

        return min(self.H_tsh,1.0)*self.power_spectrum_sw(f)
    
    def power_spectrum(self, f):
        """Calculate total power spectrum from sound waves and turbulence
        """

        return self.power_spectrum_sw(f) + self.power_spectrum_turb(f)

    def power_spectrum_conservative(self, f):
        """Calculate total power spectrum from sound waves (conservative) and turbulence
        """

        return self.power_spectrum_sw_conservative(f) + self.power_spectrum_turb(f)
    
