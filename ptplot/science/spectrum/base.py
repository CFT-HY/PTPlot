"""Base class for power spectra."""

import abc
import enum
import typing as tp

import numpy as np
from pandas import DataFrame
from pttools.bubble import DEFAULT_NU_GDH2024
from pttools.bubble.energy_budget import alpha_n_from_ubarf, ubarf_approx
from pttools.omgw0 import G0, GS0, OMEGA_PHOTON_H2, F_gw0_h2, f_star0, signal_to_noise_ratio
from pttools.omgw0 import f as f_func
from pttools.ssm import DEFAULT_N_SH, H_star_tau_nl, H_star_tau_v, J, J_old, source_lifetime_factor
from pttools.utils import copy_docstrings

from ptplot.science import const
from ptplot.science.noise import Noise, resolve_noise
import ptplot.science.type_hints as th
from ptplot.science.type_hints import FloatOrArr
from ptplot.science.utils import R_star, beta


class Engine(enum.StrEnum):
    """Enumeration of power spectrum engines."""

    BPL = DEFAULT = "bpl"
    DBPL = "dbpl"
    SSM = "ssm"

    @property
    def spectrum(self) -> "type[PowerSpectrum]":
        return ENGINE_SPECTRUM_CLASSES[self]


class PowerSpectrum(abc.ABC):
    """The base class for defining power spectra.

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
            adiabatic_index: float = const.DEFAULT_ADIABATIC_INDEX,
            zp: float = const.DEFAULT_ZP,
            k_turb: float = const.DEFAULT_K_TURB,
            parallel: bool = True):
        r"""
        Create a power spectrum.

        :param beta_over_H: $\frac{\beta}{H}$, Inverse phase transition duration relative to H
        :param T_star: $T_*$, transition temperature
        :param g_star: $g_*$, degrees of freedom
        :param v_wall: $v_\text{wall}$, wall velocity
        :param adiabatic_index: $\Gamma$, mean adiabatic index
        :param zp: $z_p$, peak angular frequency in units of the mean bubble separation
        :param alpha: $\alpha$, phase transition strength
        :param k_turb: $k_\text{turb}$, fraction of latent heat that is transformed into magnetohydrodynamic turbulence
        :param r_star: $r_*$, typical bubble radius
        :param ubarf: $\bar{U}_f$, RMS fluid velocity
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
        #: $\Gamma$, mean adiabatic index
        self.adiabatic_index: float = adiabatic_index
        #: $g_*$, degrees of freedom
        self.g_star: float = g_star
        #: $k_\text{turb}$, fraction of latent heat that is transformed into magnetohydrodynamic turbulence
        self.k_turb: float = k_turb
        #: $N_\text{sh}$, number of shock formation times
        self.N_sh: float = DEFAULT_N_SH
        #: $\nu_\text{gdh2024}$ of :giombi_2024_cs:`\ ` eq. 2.11
        self.nu_gdh2024: float = DEFAULT_NU_GDH2024
        #: Whether parallel processing is enabled
        self.parallel: bool = parallel
        #: $T_*$, transition temperature
        self.T_star: float = T_star
        #: $z_p$, peak angular frequency in units of the mean bubble separation
        self.zp: float = zp

        # Parameters that may be set
        #: $v_\text{wall}$, wall speed
        self.v_wall: float | None = v_wall

        # -----
        # Computed parameters
        # -----
        #: $\alpha$, phase transition strength
        self.alpha: float
        #: $\bar{U}_f$, RMS fluid velocity
        self.ubarf: float
        self.alpha, self.ubarf = self.validate_alpha_ubarf(
            alpha=alpha, ubarf=ubarf, v_wall=v_wall, adiabatic_index=adiabatic_index, cs=cs
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

    def csv(self, path: str | None = None, noise: Noise | None = None) -> str | None:
        """Export the power spectrum as CSV.

        :param path: A path in which to save the data
        :param noise: Which noise curve to use
        :return: If a path is not given, the data will be returned as a string.
        """
        noise = resolve_noise(noise)
        df = DataFrame({
            "f": noise.f,
            "omegaNoise": noise.noise,
            "omegaSW": self.power_spectrum(noise.f, noise=noise)[0]
        })
        return df.to_csv(path_or_buf=path)

    def f_peak(self) -> float:
        r"""Peak frequency.

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
        return tp.cast(
            float,
            f_func(z=self.zp, r_star=self.r_star, f_star0=f_star0(T_star=self.T_star, g_star=self.g_star))
        )

    def F_gw0_h2(
            self,
            g0: th.FloatOrArr = G0,
            gs0: th.FloatOrArr = GS0,
            gs_star: th.FloatOrArr | None = None,
            om_gamma0_h2: th.FloatOrArr = OMEGA_PHOTON_H2) -> th.FloatOrArr:
        return F_gw0_h2(g_star=self.g_star, g0=g0, gs0=gs0, gs_star=gs_star, om_gamma0_h2=om_gamma0_h2)

    def h_star(self) -> float:
        r"""$h_*$, inverse Hubble time at GW production, redshifted to today.

        :caprini_2015:`\ ` eq. 11
        """
        return 16.5e-6 * (self.T_star / 100) * (self.g_star / 100) ** (1 / 6)

    @property
    def H_star_tau_nl(self) -> float:
        return tp.cast(float, H_star_tau_nl(r_star=self.r_star, ubarf=self.ubarf))

    @property
    def H_star_tau_v(self) -> float:
        return tp.cast(float, H_star_tau_v(source_lifetime_factor=self.source_lifetime_factor(), nu=self.nu_gdh2024))

    @property
    def J(self) -> float:
        return tp.cast(float, J(r_star=self.r_star, H_star_tau_v=self.H_star_tau_v))

    @property
    def J_old(self) -> float:
        return tp.cast(float, J_old(r_star=self.r_star, K=self.kinetic_energy_fraction_approx))

    @property
    def kinetic_energy_fraction_approx(self) -> float:
        r"""Approximate bubble volume averaged kinetic energy fraction $K_\text{bva}$.

        $$K = \frac{{e}_{K,\text{bva}}}{\bar{e}} \approx \Gamma \bar{U}_f^2$$
        :gw_pt_ssm:`\ ` eq. B.32

        Please see :py:func:pttools.bubble.thermo.kinetic_energy_fraction: for the exact version.
        """
        return self.adiabatic_index * self.ubarf**2

    def power_spectrum_common(self, omega_tilde_gw: float = const.DEFAULT_OMEGA_TILDE_GW) -> float:
        r"""Compute the common prefactor of the power spectrum for BPL and DBPL.

        $$3h^2 F_{\text{gw},0} \Gamma^2 \bar{U}_f^4 \tilde{\Omega}_\text{gw}$$

        Please note that $F_{\text{gw},0}$ depends on the value of $h$.
        This is why the result is multiplied by $h^2$ to get a quantity that is independent of $h$.
        """
        # The equation has $(\Gamma \bar{U}_f^2)^2$,
        # which is expressed here as kinetic_energy_fraction_approx for convenience.
        # It does not equal the exact kinetic energy fraction.
        return 3 * tp.cast(float, self.F_gw0_h2()) * self.kinetic_energy_fraction_approx**2 * omega_tilde_gw

    def s[T: FloatOrArr](self, f: T) -> T:
        r"""Relative frequency $s$ with respect to the peak frequency.

        $$s = \frac{f}{f_\text{peak}}$$
        :gowling_2021:`\ ` p. 9
        """
        return tp.cast(T, f / self.f_peak())

    @staticmethod
    def snr(f: th.FloatArr1D, power_spectrum: th.FloatArr1D, noise: Noise) -> float:
        r"""Signal-to-noise ratio of a power spectrum against a noise curve.

        :param f: Frequencies $f$ of the power spectrum
        :param power_spectrum: GW power spectrum $\Omega_\text{gw} h^2$
        :param noise: Noise curve to compare against
        :return: Signal-to-noise ratio SNR, aka. $\rho$
        """
        snr, _f_noise, _noise = signal_to_noise_ratio(
            f=f,
            signal=power_spectrum,
            f_noise=noise.f,
            noise=noise.noise,
            obs_time=noise.obs_time
        )
        return snr

    def source_lifetime_factor(self) -> float:
        return tp.cast(
            float,
            source_lifetime_factor(ubarf=self.ubarf, r_star=self.r_star, N_sh=self.N_sh, nu=self.nu_gdh2024)
        )

    @staticmethod
    def validate_alpha_ubarf(
            alpha: float | None,
            ubarf: float | None,
            v_wall: float | None,
            adiabatic_index: float,
            cs: float) -> tuple[float, float]:
        if (v_wall is not None) and (alpha is not None) and (ubarf is None):
            return alpha, tp.cast(float, ubarf_approx(v_wall=v_wall, alpha_n=alpha, adiabatic_index=adiabatic_index))
        if (v_wall is not None) and (alpha is None) and (ubarf is not None):
            try:
                alpha = alpha_n_from_ubarf(v_wall=v_wall, ubarf=ubarf, cs=cs, adiabatic_index=adiabatic_index).item()
            except ValueError:
                alpha = np.nan
            return alpha, ubarf
        if (v_wall is None) and (alpha is not None) and (ubarf is not None):
            return alpha, ubarf
            # raise NotImplementedError(
            #     "Determining v_wall(alpha, ubarf) has not been implemented. "
            #     f"Got v_wall={v_wall}, alpha={alpha}, ubarf={ubarf_in}"
            # )
        raise ValueError(
            "Exactly two of v_wall, alpha, ubarf_in must be set. "
            f"Got v_wall={v_wall}, alpha={alpha}, ubarf={ubarf}.")

    @staticmethod
    def validate_beta_r_star(
            beta_over_H: float | None,
            r_star: float | None,
            v_wall: float | None,
            cs: float) -> tuple[float, float]:
        if (r_star is None) and (beta_over_H is not None and not np.isnan(beta_over_H)):
            if v_wall is None:
                raise ValueError("v_wall is required for computing r_* from beta/H.")
            # Using beta_over_H instead of beta to compute R_star gives r_star.
            return beta_over_H, tp.cast(float, R_star(beta=beta_over_H, v_wall=v_wall, cs=cs))
        if (r_star is not None and not np.isnan(r_star)) and (beta_over_H is None):
            if v_wall is None:
                raise ValueError("v_wall is required for computing beta/H from r_*.")
            # Using r_star instead of R_star to compute beta gives beta_over_H.
            return tp.cast(float, beta(R_star=r_star, v_wall=v_wall, cs=cs)), r_star
        raise ValueError(
            "Either r_star or beta_over_H must be set, but not both. "
            f"Got r_star={r_star}, beta_over_H={beta_over_H}."
        )

    # -----
    # Abstract methods
    # -----

    @abc.abstractmethod
    def power_spectrum(
            self,
            f: th.FloatArr1D,
            noise: Noise | None = None,
            log_errors: bool = False) -> tuple[th.FloatArr1D, float]:
        """GW power spectrum and its signal-to-noise ratio.

        :param f: Frequency range
        :param noise: Noise curve against which the SNR is computed.
          The default noise curve is used, if one is not given.
        :param log_errors: Log errors.
          Change the default to True when implementing a PowerSpectrum class that has error logging.
        :return: GW power spectrum, multiplied by $h^2$ and therefore independent of $h$, and its SNR.
        """


ENGINE_SPECTRUM_CLASSES: dict[Engine, type[PowerSpectrum]] = {}


copy_docstrings({
    PowerSpectrum.F_gw0_h2: F_gw0_h2,
    PowerSpectrum.H_star_tau_nl: H_star_tau_nl,
    PowerSpectrum.J: J,
    PowerSpectrum.J_old: J_old,
    PowerSpectrum.source_lifetime_factor: source_lifetime_factor
}, without_params=True)
