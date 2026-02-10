"""Ansatz for calculating the SGWB power spectra"""

import abc

from pandas import DataFrame
import numpy as np

from ptplot.science import const
from ptplot.science.engine import ENGINE_NAMES, Engine
from ptplot.science.espinosa import ubarf, ubarf_to_alpha_scalar
from ptplot.science.mission_profile import DEFAULT_MISSION_PROFILE, MissionProfile
import ptplot.science.type_hints as th
from ptplot.science.utils import beta_to_R_star


class PowerSpectrum(abc.ABC):
    """The base class for defining power spectra"""
    ENGINE: Engine = Engine.DEFAULT
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
            ubarf_in: float | None = None):
        r"""
        :param beta_over_H: Inverse phase transition duration relative to H, $\frac{\beta}{H}$
        :param T_star: Transition temperature $T_*$
        :param g_star: Degrees of freedom $g_*$
        :param vw: Wall velocity $v_\text{wall}$
        :param adiabatic_ratio: Adiabatic index $\Gamma$
        :param zp: Peak angular frequency in units of the mean bubble separation, $z_p$
        :param alpha: Phase transition strength $\alpha$
        :param k_turb: Fraction of latent heat that is transformed into magnetohydrodynamic turbulence, $k_\text{turb}$
        :param r_star: Typical bubble radius
        :param ubarf_in: rms fluid velocity $\bar{U}_f$
        """
        if g_star is None or np.isnan(g_star):
            raise ValueError(f"Invalid g_star={g_star}")
        if T_star is None or np.isnan(T_star):
            raise ValueError(f"Invalid T_star={T_star}")

        # Parameters that are guaranteed to be set
        self.adiabatic_ratio: float = adiabatic_ratio
        self.g_star: float = g_star
        self.k_turb: float = k_turb
        self.T_star: float = T_star
        self.zp: float = zp

        # Parameters that may be set
        self.vw: float | None = vw
        self.beta_over_H: float | None = beta_over_H

        # -----
        # Computed parameters
        # -----

        self.alpha: float
        self.ubarf: float
        if (vw is not None) and (alpha is not None) and (ubarf_in is None):
            self.alpha = alpha
            self.ubarf = ubarf(vw, alpha, adiabatic_ratio)
        elif (vw is not None) and (alpha is None) and (ubarf_in is not None):
            self.alpha = ubarf_to_alpha_scalar(vw=vw, this_ubarf=ubarf_in, adiabaticRatio=adiabatic_ratio)
            self.ubarf = ubarf_in
        elif (vw is None) and (alpha is not None) and (ubarf_in is not None):
            self.alpha = alpha
            self.ubarf = ubarf_in
            # raise NotImplementedError(
            #     "Determining vw(alpha, ubarf) has not been implemented. "
            #     f"Got vw={vw}, alpha={alpha}, ubarf={ubarf_in}"
            # )
        else:
            raise ValueError(
                "Exactly two of vw, alpha, ubarf_in must be set. "
                f"Got vw={vw}, alpha={alpha}, ubarf={ubarf_in}.")

        # Calculate typical bubble radius
        self.r_star: float
        if (r_star is None) and (beta_over_H is not None and not np.isnan(beta_over_H)):
            self.r_star = beta_to_R_star(self.beta_over_H, self.vw)
        elif (r_star is not None and not np.isnan(r_star)) and (beta_over_H is None):
            self.r_star = r_star
        else:
            raise ValueError(
                "Either r_star or beta_over_H must be set, but not both. "
                f"Got r_star={r_star}, beta_over_H={beta_over_H}."
            )

        self.h_star: float = 16.5e-6 * (self.T_star / 100) * (self.g_star / 100)**(1/6)

        #: Shock time
        self.H_tsh: float = self.r_star / self.ubarf

    def csv(self, path: str | None = None, mission_profile: MissionProfile = DEFAULT_MISSION_PROFILE) -> str | None:
        """Export the power spectrum as CSV

        :param path: A path in which to save the data
        :param mission_profile: Which sensitivity curve to use
        :return: If a path is not given, the data will be returned as a string.
        """
        df = DataFrame({
            "f": mission_profile.f,
            "omegaSens": mission_profile.sensitivity,
            "omegaSW": self.power_spectrum(mission_profile.f)
        })
        return df.to_csv(path_or_buf=path)

    @property
    def shock_time(self) -> float:
        """Shock time"""
        return self.H_tsh

    @abc.abstractmethod
    def power_spectrum(self, f: th.FloatOrArr) -> th.FloatOrArr:
        """GW power spectrum"""
        pass
