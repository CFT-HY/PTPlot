"""Base class for power spectra."""

import abc
import logging
import typing as tp

import numpy as np
from pandas import DataFrame
from pttools.bubble import DEFAULT_NU_GDH2024, SolutionType
from pttools.bubble.energy_budget import alpha_n_from_ubarf, ubarf_approx
from pttools.models import Model
from pttools.omgw0 import (
    G0,
    GS0,
    OMEGA_PHOTON_H2,
    F_gw0_h2,
    f_star0,
    signal_to_noise_ratio,
)
from pttools.omgw0 import f as f_func
from pttools.ssm import (
    DEFAULT_N_SH,
    H_star_eta_sh,
    H_star_eta_v,
    J,
    J_old,
    source_lifetime_factor,
)
from pttools.ssm import beta_tilde as beta_tilde_func
from pttools.ssm import r_star as r_star_func
from pttools.utils import copy_docstrings

from ptplot.science import const
from ptplot.science.noise import Noise, resolve_noise
from ptplot.science.type_hints import FloatArr1D, FloatOrArr

if tp.TYPE_CHECKING:
    from ptplot.science.spectrum.engine import Engine

logger: logging.Logger = logging.getLogger(__name__)


class PowerSpectrum(abc.ABC):
    """The base class for defining power spectra.

    When adding a new power spectrum class, please add it to the Engine enum.
    """

    COLOR: str
    ENGINE: Engine
    NAME: str
    SHORT_NAME: str

    OLD_J: bool = False
    REQUIRE_V_WALL: bool = False
    REQUIRE_SOUND_SHELL_THICKNESS: bool = False

    #: Efficiency of producing bulk kinetic energy relative to a single bubble.
    #: Used by :py:class:`ptplot.science.spectrum.PowerSpectrumDBPL2024`.
    K_EFFICIENCY: float = 1.

    def __init__(
            self,
            # Primary parameters
            T_star: float = const.DEFAULT_T_STAR,
            g_star: float = const.DEFAULT_G_STAR,
            v_wall: float | None = None,
            alpha: float | None = None,
            beta_tilde: float | None = None,
            ubarf: float | None = None,
            r_star: float | None = None,
            # Additional parameters
            cs: float = const.CS0,  # Todo: implement this properly
            adiabatic_index: float = const.DEFAULT_ADIABATIC_INDEX,
            zp: float = const.DEFAULT_ZP,
            k_turb: float = const.DEFAULT_K_TURB,
            nu_gdh2024: float = DEFAULT_NU_GDH2024,
            # Switches
            legacy_nucleation_cs_max: bool = False,
            parallel: bool = True):
        r"""
        Create a power spectrum.

        :param beta_tilde: $\frac{\beta}{H}$, Inverse phase transition duration relative to $H_*$
        :param T_star: $T_*$, transition temperature
        :param g_star: $g_*$, degrees of freedom
        :param v_wall: $v_\text{wall}$, wall velocity
        :param cs: $c_s$, sound speed. Used in this base class for:
            1) validation of sound shell thickness,
            2) $\alpha \leftrightarrow \bar{U}_\text{f}$ conversion
            3) $\tilde{\beta} \leftrightarrow r_*$ conversion if ``legacy_nucleation_cs_max`` is enabled
        :param adiabatic_index: $\Gamma$, mean adiabatic index
        :param zp: $z_p$, peak angular frequency in units of the mean bubble separation
        :param alpha: $\alpha$, phase transition strength
        :param k_turb: $k_\text{turb}$, fraction of latent heat that is transformed into magnetohydrodynamic turbulence
        :param r_star: $r_*$, typical bubble radius
        :param nu_gdh2024: $\nu_\text{gdh2024}$ of :giombi_2024_cs:`\ ` eq. 2.11
        :param ubarf: $\bar{U}_f$, RMS fluid velocity
        :param legacy_nucleation_cs_max:
            Use legacy $\max(v_{\text{wall}}, c_s)$ in $\tilde{\beta} \leftrightarrow r_*$ conversion
        :param parallel: Enable parallel processing for this spectrum if the engine supports it.
            This should be disabled when generating multiple spectra in parallel.
        """
        if g_star is None or np.isnan(g_star):
            raise ValueError(f"Invalid g_star={g_star}")
        if T_star is None or np.isnan(T_star):
            raise ValueError(f"Invalid T_star={T_star}")

        # Parameters that are guaranteed to be set
        #: $\Gamma$, mean adiabatic index
        self.adiabatic_index: float = adiabatic_index
        #: $c_s$, speed of sound
        self.cs: float = cs
        #: $g_*$, degrees of freedom
        self.g_star: float = g_star
        #: $k_\text{turb}$, fraction of latent heat that is transformed into magnetohydrodynamic turbulence
        self.k_turb: float = k_turb
        #: $N_\text{sh}$, number of shock formation times
        self.N_sh: float = DEFAULT_N_SH
        #: $\nu_\text{gdh2024}$ of :giombi_2024_cs:`\ ` eq. 2.11
        self.nu_gdh2024: float = nu_gdh2024
        #: Whether parallel processing is enabled
        self.parallel: bool = parallel
        #: $T_*$, transition temperature
        self.T_star: float = T_star
        #: $z_p$, peak angular frequency in units of the mean bubble separation
        self.zp: float = zp

        # Parameters that may be set
        #: $v_\text{wall}$, wall speed
        self.v_wall: float | None = self.validate_v_wall(v_wall=v_wall, cs=cs)

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
        self.beta_tilde: float
        #: Given $\tilde{\beta} \equiv \frac{\beta}{H_*}$, not computed
        self.beta_tilde_given: float | None = beta_tilde
        #: Hubble-scaled mean bubble spacing $r_*$
        self.r_star: float
        #: Given $r_*$, not computed
        self.r_star_given: float | None = r_star
        self.beta_tilde, self.r_star = self.validate_beta_r_star(
            beta_tilde=beta_tilde, r_star=r_star, v_wall=v_wall, legacy_cs=cs if legacy_nucleation_cs_max else None
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
            g0: FloatOrArr = G0,
            gs0: FloatOrArr = GS0,
            gs_star: FloatOrArr | None = None,
            om_gamma0_h2: FloatOrArr = OMEGA_PHOTON_H2) -> FloatOrArr:
        return F_gw0_h2(g_star=self.g_star, g0=g0, gs0=gs0, gs_star=gs_star, om_gamma0_h2=om_gamma0_h2)

    def h_star(self) -> float:
        r"""$h_*$, inverse Hubble time at GW production, redshifted to today.

        :caprini_2016:`\ ` eq. 11
        """
        return 16.5e-6 * (self.T_star / 100) * (self.g_star / 100) ** (1 / 6)

    @property
    def H_star_eta_sh(self) -> float:
        return H_star_eta_sh(r_star=self.r_star, ubarf=self.ubarf)

    @property
    def H_star_eta_v(self) -> float:
        return H_star_eta_v(source_lifetime_factor=self.source_lifetime_factor(), nu=self.nu_gdh2024)

    def J(self, old: bool | None = None) -> float:
        r"""Combined lifetime factor $J$.

        $$J \equiv r_* \mathcal{H}_* \eta_\text{v}$$.

        This is defined as
        :py:func:`pttools.ssm.scaling.J` or
        :py:func:`pttools.ssm.scaling.J_old`
        depending on the model.
        """
        if self.OLD_J if old is None else old:
            return J_old(r_star=self.r_star, K=self.kinetic_energy_fraction)
        return J(r_star=self.r_star, H_star_eta_v=self.H_star_eta_v)

    @property
    def kinetic_energy_fraction(self) -> float:
        r"""Bubble volume averaged kinetic energy fraction $K_\text{bva}$.

        This is computed as
        $$K = \frac{{e}_{K,\text{bva}}}{\bar{e}} \approx \Gamma \bar{U}_f^2$$
        :gw_pt_ssm:`\ ` eq. B.32,
        unless overwritten for a particular model.
        Since $\bar{U}_f$ is computed in
        :py:meth:`PowerSpectrum.validate_alpha_ubarf_static` with
        :py:func:`pttools.bubble.energy_budget.ubarf_approx`,
        this corresponds exactly to
        :py:func:`pttools.bubble.energy_budget.kinetic_energy_fraction_approx`.

        Please see :py:func:pttools.bubble.thermo.kinetic_energy_fraction: for the exact version.
        """
        return self.K_EFFICIENCY * self.adiabatic_index * self.ubarf**2

    def power_spectrum_common(self, omega_tilde_gw: float = const.DEFAULT_OMEGA_TILDE_GW) -> float:
        r"""Compute the common prefactor of the power spectrum for BPL2020 and DBPL2021.

        $$3h^2 F_{\text{gw},0} \Gamma^2 \bar{U}_f^4 \tilde{\Omega}_\text{gw}$$

        Note that $F_{\text{gw},0}$ depends on the value of $h$.
        This is why the result is multiplied by $h^2$ to get a quantity that is independent of $h$.

        Note that this equation has $(\Gamma \bar{U}_f^2)^2$,
        which does not exactly equal the kinetic energy fraction $K$.
        """
        return 3 * tp.cast(float, self.F_gw0_h2()) * (self.adiabatic_index * self.ubarf**2)**2 * omega_tilde_gw

    def s[T: FloatOrArr](self, f: T) -> T:
        r"""Relative frequency $s$ with respect to the peak frequency.

        $$s = \frac{f}{f_{\text{peak}}}$$
        :gowling_2021:`\ ` p. 9
        """
        return tp.cast(T, f / self.f_peak())

    @staticmethod
    def snr(f: FloatArr1D, power_spectrum: FloatArr1D, noise: Noise) -> float:
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
    def validate_alpha_ubarf_static(
            alpha: float | None,
            ubarf: float | None,
            v_wall: float | None,
            adiabatic_index: float,
            cs: float,
            v_cj: float | None = None,
            model: Model | None = None) -> tuple[float, float]:
        if (v_wall is not None) and (alpha is not None) and (ubarf is None):
            return alpha, tp.cast(float,
                ubarf_approx(
                    v_wall=v_wall,
                    alpha_n=alpha,
                    model=model,
                    cs=cs,
                    v_cj=v_cj,
                    adiabatic_index=adiabatic_index
                )
            )
        if (v_wall is not None) and (alpha is None) and (ubarf is not None):
            try:
                alpha = alpha_n_from_ubarf(
                    v_wall=v_wall,
                    ubarf=ubarf,
                    model=model,
                    cs=cs,
                    adiabatic_index=adiabatic_index
                ).item()
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

    def validate_alpha_ubarf(
            self,
            alpha: float | None,
            ubarf: float | None,
            v_wall: float | None,
            adiabatic_index: float,
            cs: float,
            v_cj: float | None = None,
            model: Model | None = None) -> tuple[float, float]:
        r"""Validate $\alpha$ and $\bar{U}_\text{f}$."""
        return self.validate_alpha_ubarf_static(
            alpha=alpha, ubarf=ubarf, v_wall=v_wall, adiabatic_index=adiabatic_index, cs=cs, v_cj=v_cj, model=model
        )

    def validate_beta_r_star(
            self,
            beta_tilde: float | None,
            r_star: float | None,
            v_wall: float | None,
            xi: FloatArr1D | None = None,
            T: FloatArr1D | None = None,
            sol_type: SolutionType = SolutionType.DETON,
            legacy_cs: float | None = None) -> tuple[float, float]:
        r"""Validate $\tilde{\beta}$ and $r_*$."""
        if (r_star is None) and (beta_tilde is not None and not np.isnan(beta_tilde)):
            if v_wall is None:
                raise ValueError("v_wall is required for computing r_* from beta/H.")
            return beta_tilde, tp.cast(float, r_star_func(
                beta_tilde=beta_tilde, v_wall=v_wall, xi=xi, T=T, sol_type=sol_type, legacy_cs=legacy_cs)
            )
        if (r_star is not None and not np.isnan(r_star)) and (beta_tilde is None):
            if v_wall is None:
                raise ValueError("v_wall is required for computing beta/H from r_*.")
            return tp.cast(float, beta_tilde_func(r_star=r_star, v_wall=v_wall, legacy_cs=legacy_cs)), r_star
        raise ValueError(
            "Either r_star or beta_tilde must be set, but not both. "
            f"Got r_star={r_star}, beta_tilde={beta_tilde}."
        )

    def validate_v_wall(self, v_wall: float | None, cs: float = const.CS0) -> float | None:
        r"""Validate $v_\text{wall}$."""
        if v_wall is None or np.isnan(v_wall):
            if self.REQUIRE_V_WALL:
                raise ValueError(f"{self.ENGINE.name} requires v_wall to be set. Got v_wall={v_wall}.")
        elif v_wall < 0 or v_wall >= 1:
            raise ValueError(f"Invalid v_wall={v_wall}")
        elif np.isclose(v_wall, cs):
            msg = f"The sound shell thickness is zero for v_wall=cs={cs}."
            if self.REQUIRE_SOUND_SHELL_THICKNESS:
                raise ValueError(msg)
            logger.error(msg)

        return v_wall

    # -----
    # Abstract methods
    # -----

    @abc.abstractmethod
    def power_spectrum(
            self,
            f: FloatArr1D,
            noise: Noise | None = None,
            log_errors: bool = False) -> tuple[FloatArr1D, float]:
        """GW power spectrum and its signal-to-noise ratio.

        :param f: Frequency range
        :param noise: Noise curve against which the SNR is computed.
          The default noise curve is used, if one is not given.
        :param log_errors: Log errors.
          Change the default to True when implementing a PowerSpectrum class that has error logging.
        :return: GW power spectrum, multiplied by $h^2$ and therefore independent of $h$, and its SNR.
        """


copy_docstrings({
    PowerSpectrum.F_gw0_h2: F_gw0_h2,
    PowerSpectrum.H_star_eta_sh: H_star_eta_sh,
    PowerSpectrum.source_lifetime_factor: source_lifetime_factor
}, without_params=True)
