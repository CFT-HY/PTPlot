"""Ansatz for calculating the SGWB power spectra"""

import abc

import numpy as np

from ptplot.science import const
from ptplot.science.engine import ENGINE_NAMES, Engine
from ptplot.science.espinosa import ubarf
from ptplot.science.utils import beta_to_R_star


class PowerSpectrum(abc.ABC):
    """The base class for defining power spectra

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
    ENGINE: Engine = Engine.DEFAULT
    NAME: str = ENGINE_NAMES[ENGINE]
    SHORT_NAME: str = ENGINE.name

    def __init__(
        self,
        beta_over_H: float = None,
        T_star: float = const.DEFAULT_T_STAR,
        g_star: float = const.DEFAULT_G_STAR,
        vw: float = None,
        adiabatic_ratio: float = const.DEFAULT_ADIABATIC_RATIO,
        zp: float = const.DEFAULT_ZP,
        alpha: float = None,
        k_turb: float = const.DEFAULT_K_TURB,
        r_star: float = None,
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
        r_star : float
            Typical bubble radius
        ubarf_in : float
            Input value of the rms fluid velocity
        """
        if g_star is None:
            raise ValueError(f"Invalid g_star={g_star}")

        # Parameters that are guaranteed to be set
        self.adiabatic_ratio: float = adiabatic_ratio
        self.g_star: float = g_star
        self.k_turb: float = k_turb
        self.T_star: float = T_star
        self.zp: float = zp

        # Parameters that may be set
        self.alpha: float | None = alpha
        self.vw: float | None = vw
        self.beta_over_H: float | None = beta_over_H

        # -----
        # Computed parameters
        # -----

        # Either take ubarf_in as-is, or calculate ubarf from the wall velocity
        self.ubarf: float
        if (vw is not None) and (ubarf_in is None):
            self.ubarf = ubarf(vw, alpha, adiabatic_ratio)
        elif (vw is None) and (ubarf_in is not None):
            self.ubarf = ubarf_in
        else:
            raise ValueError("Either ubarf_in or vw must be set, but not both")

        # Calculate typical bubble radius
        self.r_star: float
        if (r_star is None) and (beta_over_H is not None):
            self.r_star = beta_to_R_star(self.beta_over_H, self.vw)
        elif (r_star is not None) and (beta_over_H is None):
            self.r_star = r_star
        else:
            raise ValueError("Either H_rstar or beta_over_H must be set, but not both")

        self.h_star: float = 16.5e-6 * (self.T_star / 100.0) * np.power(self.g_star / 100.0, 1.0 / 6.0)

        #: Shock time
        self.H_tsh: float = self.r_star / self.ubarf

    def get_shock_time(self) -> float:
        """Calculate shock time"""
        return self.H_tsh
