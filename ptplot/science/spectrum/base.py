"""Base class for power spectra"""

import abc
import enum

import numpy as np
from pandas import DataFrame
from pttools.bubble import DEFAULT_NU_GDH2024
from pttools.omgw0 import G0, GS0, OMEGA_PHOTON, f as f_func, f_star0, F_gw0
from pttools.ssm import DEFAULT_N_SH, H_star_tau_v, J, source_lifetime_factor
from pttools.utils import copy_docstrings

from ptplot.science import const
from ptplot.science.espinosa import ubarf as ubarf_func, alpha_n_from_ubarf
from ptplot.science.mission_profile import DEFAULT_MISSION_PROFILE, MissionProfile
import ptplot.science.type_hints as th
from ptplot.science.type_hints import FloatOrArr, FloatOrArr1D
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
            k_turb: float = const.DEFAULT_K_TURB,
            parallel: bool = True):
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
        :param parallel: Enable parallel processing for this spectrum if the engine supports it.
            This should be disabled when generating multiple spectra in parallel.
        """
        if g_star is None or np.isnan(g_star):
            raise ValueError(f"Invalid g_star={g_star}")
        if T_star is None or np.isnan(T_star):
            raise ValueError(f"Invalid T_star={T_star}")
        if not (v_wall is None or 0 < v_wall <= 1):
            raise ValueError(f"Invalid v_wall={v_wall}")

        # Parameters that are guaranteed to be set
        self.adiabatic_ratio: float = adiabatic_ratio
        self.g_star: float = g_star
        self.k_turb: float = k_turb
        self.N_sh: float = DEFAULT_N_SH
        self.nu_gdh2024: float = DEFAULT_NU_GDH2024
        self.parallel: bool = parallel
        self.T_star: float = T_star
        self.zp: float = zp

        # Parameters that may be set
        self.v_wall: float | None = v_wall

        # -----
        # Computed parameters
        # -----
        #: $\alpha$
        self.alpha: float
        #: $\bar{U}_f$
        self.ubarf: float
        self.alpha, self.ubarf = self.validate_alpha_ubarf(
            alpha=alpha, ubarf=ubarf, v_wall=v_wall, adiabatic_ratio=adiabatic_ratio, cs=cs
        )
        #: $\tilde{\beta} \equiv \frac{\beta}{H_*}$, inverse phase transition duration relative to Hubble time
        self.beta_over_H: float
        #: Given $\tilde{\beta} \equiv \frac{\beta}{H_*}$, not computed
        self.beta_over_H_given: float | None = beta_over_H
        #: Hubble-scaled mean bubble spacing $r_*$
        self.r_star: float
        #: Given $r_*$, not computed
        self.r_star_given: float | None = r_star
        self.beta_over_H, self.r_star = self.validate_beta_r_star(
            beta_over_H=beta_over_H, r_star=r_star, v_wall=v_wall, cs=cs
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
        return f_func(z=self.zp, r_star=self.r_star, f_star0=f_star0(T_star=self.T_star, g_star=self.g_star))

    def F_gw0(  # pylint: disable=missing-function-docstring
            self,
            g0: th.FloatOrArr = G0,
            gs0: th.FloatOrArr = GS0,
            gs_star: th.FloatOrArr | None = None,
            om_gamma0: th.FloatOrArr = OMEGA_PHOTON) -> th.FloatOrArr:
        return F_gw0(g_star=self.g_star, g0=g0, gs0=gs0, gs_star=gs_star, om_gamma0=om_gamma0)

    def h_star(self) -> float:
        r"""$h_*$, inverse Hubble time at GW production, redshifted to today
        :caprini_2015:`\ ` eq. 11
        """
        return 16.5e-6 * (self.T_star / 100) * (self.g_star / 100) ** (1 / 6)

    def J(
            self,
            nu: th.FloatOrArr = DEFAULT_NU_GDH2024) -> th.FloatOrArr:  # pylint: disable=missing-function-docstring
        return J(
            r_star=self.r_star,
            H_star_tau_v=H_star_tau_v(nu=nu, source_lifetime_factor=self.source_lifetime_factor())
        )

    @property
    def kinetic_energy_fraction_approx(self) -> float:
        r"""Approximate bubble volume averaged kinetic energy fraction $K_\text{bva}$
        $$K = \frac{{e}_{K,\text{bva}}}{\bar{e}} \approx \Gamma \bar{U}_f^2$$
        :gw_pt_ssm:`\ ` eq. B.32

        Please see :py:func:pttools.bubble.thermo.kinetic_energy_fraction: for the exact version.
        """
        return self.adiabatic_ratio * self.ubarf**2

    def power_spectrum_common(self, omega_tilde_gw: float = const.DEFAULT_OMEGA_TILDE_GW) -> float:
        r"""Common prefactor of the power spectrum for BPL and DBPL
        $$3h^2 F_{\text{gw},0} \Gamma^2 \bar{U}_f^4 \tilde{\Omega}_\text{gw}$$

        Please note that $F_{\text{gw},0}$ depends on the value of $h$.
        This is why the result is multiplied by $h^2$ to get a quantity that is independent of $h$.
        """
        # The equation has $(\Gamma \bar{U}_f^2)^2$,
        # which is expressed here as kinetic_energy_fraction_approx for convenience.
        # It does not equal the exact kinetic energy fraction.
        return 3 * const.H2 * self.F_gw0() * self.kinetic_energy_fraction_approx**2 * omega_tilde_gw

    def s[T: FloatOrArr](self, f: T) -> T:
        r"""Relative frequency $s$ with respect to the peak frequency

        $$s = \frac{f}{f_\text{peak}}$$
        :gowling_2021:`\ ` p. 9
        """
        return f / self.f_peak()

    def source_lifetime_factor(self) -> float:
        return source_lifetime_factor(ubarf=self.ubarf, r_star=self.r_star, N_sh=self.N_sh, nu=self.nu_gdh2024)

    @staticmethod
    def validate_alpha_ubarf(
            alpha: float | None,
            ubarf: float | None,
            v_wall: float | None,
            adiabatic_ratio: float,
            cs: float) -> tuple[float, float]:
        if (v_wall is not None) and (alpha is not None) and (ubarf is None):
            return alpha, ubarf_func(v_wall=v_wall, alpha_n=alpha, adiabatic_ratio=adiabatic_ratio)
        if (v_wall is not None) and (alpha is None) and (ubarf is not None):
            try:
                alpha = alpha_n_from_ubarf(v_wall=v_wall, ubarf=ubarf, cs=cs, adiabatic_ratio=adiabatic_ratio).item()
            except ValueError:
                alpha = np.nan
            return alpha, ubarf
        if (v_wall is None) and (alpha is not None) and (ubarf is not None):
            return alpha, ubarf
            # raise NotImplementedError(
            #     "Determining v_wall(alpha, ubarf) has not been implemented. "
            #     f"Got v_wall={v_wall}, alpha={alpha}, ubarf={ubarf_in}"
            # )
        else:
            raise ValueError(
                "Exactly two of v_wall, alpha, ubarf_in must be set. "
                f"Got v_wall={v_wall}, alpha={alpha}, ubarf={ubarf}.")

    def validate_beta_r_star(
            self,
            beta_over_H: float | None,
            r_star: float | None,
            v_wall: float | None,
            cs: float) -> tuple[float, float]:
        if (r_star is None) and (beta_over_H is not None and not np.isnan(beta_over_H)):
            # Using beta_over_H instead of beta to compute R_star gives r_star.
            return beta_over_H, R_star(beta=beta_over_H, v_wall=v_wall, cs=cs)
        if (r_star is not None and not np.isnan(r_star)) and (beta_over_H is None):
            # Using r_star instead of R_star to compute beta gives beta_over_H.
            return beta(R_star=r_star, v_wall=v_wall, cs=cs), r_star
        raise ValueError(
            "Either r_star or beta_over_H must be set, but not both. "
            f"Got r_star={r_star}, beta_over_H={beta_over_H}."
        )

    # -----
    # Properties
    # -----

    @property
    def shock_time(self) -> float:
        """Shock time"""
        return self.H_tsh

    # -----
    # Abstract methods
    # -----

    @abc.abstractmethod
    def power_spectrum[T: FloatOrArr1D](self, f: T, log_errors: bool = False) -> T:
        """GW power spectrum

        :param f: Frequency range
        :param log_errors: Log errors.
          Change the default to True when implementing a PowerSpectrum class that has error logging.
        :return: GW power spectrum, multiplied by $h^2$ and therefore independent of $h$.
        """


ENGINE_SPECTRUM_CLASSES: dict[Engine, type[PowerSpectrum]] = {}


copy_docstrings({
    PowerSpectrum.F_gw0: F_gw0,
    PowerSpectrum.J: J,
    PowerSpectrum.source_lifetime_factor: source_lifetime_factor
}, without_params=True)
