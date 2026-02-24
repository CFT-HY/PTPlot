"""Base class for power spectra"""

import abc
import enum

import numpy as np
from pandas import DataFrame
from pttools.omgw0 import G0, GS0, OMEGA_RADIATION, f, f_star0, F_gw0, J
from pttools.utils import copy_docstrings_without_params

from ptplot.science import const
from ptplot.science.espinosa import ubarf as ubarf_func, alpha_n_from_ubarf
from ptplot.science.mission_profile import DEFAULT_MISSION_PROFILE, MissionProfile
import ptplot.science.type_hints as th
from ptplot.science.type_hints import FloatArr
from ptplot.science.utils import beta, R_star


class Engine(enum.StrEnum):
    """Enumeration of power spectrum engines"""
    BPL = DEFAULT = "bpl"
    DBPL = "dbpl"
    SSM = "ssm"

    @property
    def spectrum(self) -> "type[PowerSpectrum]":
        return ENGINE_SPECTRUM_CLASSES[self]


class PowerSpectrum(abc.ABC):
    """The base class for defining power spectra

    When adding a new power spectrum class, please add it to the Engine enum.
    """
    COLOR: str
    ENGINE: Engine
    NAME: str
    SHORT_NAME: str

    def __init__(
            self,
            T_star: float = const.DEFAULT_T_STAR,
            g_star: float = const.DEFAULT_G_STAR,
            v_wall: float | None = None,
            alpha: float | None = None,
            beta_over_H: float | None = None,
            ubarf: float | None = None,
            r_star: float | None = None,
            cs: float = const.CS0,  # Todo: implement this properly
            adiabatic_ratio: float = const.DEFAULT_ADIABATIC_RATIO,
            zp: float = const.DEFAULT_ZP,
            k_turb: float = const.DEFAULT_K_TURB):
        r"""
        :param beta_over_H: Inverse phase transition duration relative to H, $\frac{\beta}{H}$
        :param T_star: Transition temperature $T_*$
        :param g_star: Degrees of freedom $g_*$
        :param v_wall: Wall velocity $v_\text{wall}$
        :param adiabatic_ratio: Adiabatic index $\Gamma$
        :param zp: Peak angular frequency in units of the mean bubble separation, $z_p$
        :param alpha: Phase transition strength $\alpha$
        :param k_turb: Fraction of latent heat that is transformed into magnetohydrodynamic turbulence, $k_\text{turb}$
        :param r_star: Typical bubble radius
        :param ubarf: rms fluid velocity $\bar{U}_f$
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
        self.v_wall: float | None = v_wall

        # -----
        # Computed parameters
        # -----

        self.alpha: float
        self.ubarf: float
        if (v_wall is not None) and (alpha is not None) and (ubarf is None):
            self.alpha = alpha
            self.ubarf = ubarf_func(v_wall=v_wall, alpha_n=alpha, adiabatic_ratio=adiabatic_ratio)
        elif (v_wall is not None) and (alpha is None) and (ubarf is not None):
            try:
                self.alpha = alpha_n_from_ubarf(v_wall=v_wall, ubarf=ubarf, cs=cs, adiabatic_ratio=adiabatic_ratio).item()
            except ValueError:
                self.alpha = np.nan
            self.ubarf = ubarf
        elif (v_wall is None) and (alpha is not None) and (ubarf is not None):
            self.alpha = alpha
            self.ubarf = ubarf
            # raise NotImplementedError(
            #     "Determining v_wall(alpha, ubarf) has not been implemented. "
            #     f"Got v_wall={v_wall}, alpha={alpha}, ubarf={ubarf_in}"
            # )
        else:
            raise ValueError(
                "Exactly two of v_wall, alpha, ubarf_in must be set. "
                f"Got v_wall={v_wall}, alpha={alpha}, ubarf={ubarf}.")

        #: Hubble-scaled mean bubble spacing $r_*$
        self.r_star: float
        #: $\frac{\beta}{H_*}$, inverse phase transition duration relative to Hubble time
        self.beta_over_H: float

        if (r_star is None) and (beta_over_H is not None and not np.isnan(beta_over_H)):
            self.beta_over_H = beta_over_H
            # Using beta_over_H instead of beta to compute R_star gives r_star.
            self.r_star = R_star(beta=beta_over_H, v_wall=self.v_wall, cs=cs)
        elif (r_star is not None and not np.isnan(r_star)) and (beta_over_H is None):
            # Using r_star instead of R_star to compute beta gives beta_over_H.
            self.beta_over_H = beta(R_star=r_star, v_wall=self.v_wall, cs=cs)
            self.r_star = r_star
        else:
            raise ValueError(
                "Either r_star or beta_over_H must be set, but not both. "
                f"Got r_star={r_star}, beta_over_H={beta_over_H}."
            )

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

    def f_peak(self) -> float:
        r"""Peak frequency

        $$f_{p,0} \approx 26
        \left( \frac{1}{H_* R_*} \right)
        \left( \frac{z_p}{10} \right)
        \left( \frac{T_*}{100 \text{GeV}} \right)
        \left( \frac{g_*}{100} \right)^{1/6}
        \text{µHz}$$
        :hindmarsh_2017:`\ ` eq. 43
        :caprini_2020:`\ ` eq. 31
        These equations are equivalent to :gowling_2021:`\ ` eq. 2.12, 2.13.

        :return: Peak frequency $f_\text{peak}$ in Hz
        """
        return f(z=self.zp, r_star=self.r_star, f_star0=f_star0(Tn=self.T_star, g_star=self.g_star))

    def F_gw0(  # pylint: disable=missing-function-docstring
            self,
            g0: th.FloatOrArr = G0,
            gs0: th.FloatOrArr = GS0,
            gs_star: th.FloatOrArr = None,
            om_gamma0: th.FloatOrArr = OMEGA_RADIATION) -> th.FloatOrArr:
        return F_gw0(g_star=self.g_star, g0=g0, gs0=gs0, gs_star=gs_star, om_gamma0=om_gamma0)

    def h_star(self) -> float:
        r"""$h_*$, inverse Hubble time at GW production, redshifted to today
        :caprini_2015:`\ ` eq. 11
        """
        return 16.5e-6 * (self.T_star / 100) * (self.g_star / 100) ** (1 / 6)

    def J[T: (float, FloatArr)](self, nu: T = 0.) -> T:  # pylint: disable=missing-function-docstring
        return J(r_star=self.r_star, K_frac=self.K(), nu=nu)

    def K(self) -> float:
        r"""Kinetic energy fraction $K$

        $$K = \frac{\langle w \gamma^2 v^2 \rangle}{\bar{e}} = \Gamma \bar{U}_f^2$$
        :caprini_2020:`\ ` eq. 22
        """
        return self.adiabatic_ratio * self.ubarf**2

    def power_spectrum_common(self, omega_tilde_gw: float = const.DEFAULT_OMEGA_TILDE_GW) -> float:
        r"""Common prefactor of the power spectrum for BPL and DBPL

        $$3h^2 F_{\text{gw},0} K^2 \tilde{\Omega}_\text{gw}
        = 3h^2 F_{\text{gw},0} \Gamma^2 \bar{U}_f^4 \tilde{\Omega}_\text{gw}$$

        Please note that $F_{\text{gw},0}$ depends on the value of $h$.
        This is why the result is multiplied by $h^2$ to get a quantity that is independent of $h$.
        """
        return 3 * const.H_PLANCK2 * self.F_gw0() * self.K()**2 * omega_tilde_gw

    def s[T: (float, FloatArr)](self, f: T) -> T:
        r"""Relative frequency $s$ with respect to the peak frequency

        $$s = \frac{f}{f_\text{peak}}$$
        :gowling_2021:`\ ` p. 9
        """
        return f / self.f_peak()

    @property
    def shock_time(self) -> float:
        """Shock time"""
        return self.H_tsh

    @abc.abstractmethod
    def power_spectrum(self, f: th.FloatOrArr) -> th.FloatOrArr:
        """GW power spectrum"""


ENGINE_SPECTRUM_CLASSES: dict[Engine, type[PowerSpectrum]] = {}


copy_docstrings_without_params({
    PowerSpectrum.F_gw0: F_gw0,
    PowerSpectrum.J: J
})
