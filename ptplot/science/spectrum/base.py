"""Base class for power spectra."""

import abc
import logging
import typing as tp
import uuid

import numpy as np
from pandas import DataFrame
from pttools.bubble import DEFAULT_NU_GDH2024, SolutionType
from pttools.bubble.energy_budget import alpha_n_from_ubarf, ubarf_approx
from pttools.export import Extractor, Record
from pttools.models import Model
from pttools.omgw0 import (
    GE0_PHOTON,
    GS0,
    OMEGA_PHOTON_H2,
    F_gw0_h2,
    signal_to_noise_ratio,
)
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
from pttools.utils.fields import Extractable, Fields

from ptplot.science.const import CS0, DEFAULT_ADIABATIC_INDEX, DEFAULT_G_STAR, DEFAULT_T_STAR
from ptplot.science.noise import Noise, resolve_noise
from ptplot.science.spectrum.export import POWER_SPECTRUM_FIELDS
from ptplot.science.type_hints import FloatArr1D, FloatOrArr

if tp.TYPE_CHECKING:
    from ptplot.science.spectrum.engine import Engine

logger: logging.Logger = logging.getLogger(__name__)


class PowerSpectrum(Extractable, abc.ABC):
    """The base class for defining power spectra.

    When adding a new power spectrum class, please add it to the Engine enum.
    The spectra can be exported with :py:class:`pttools.export.exporter.Exporter`,
    if the class has a :py:attr:`TABLE`, see :py:meth:`record`.
    """

    FIELDS: tp.ClassVar[Fields] = POWER_SPECTRUM_FIELDS
    #: Name of the table of the spectra of this engine in the exported files.
    #: Each engine has a table of its own, as all the objects of a table must be of the same class.
    #: If None, the spectra are not exported as such, see :py:meth:`record`.
    TABLE: tp.ClassVar[str | None] = None

    COLOR: tp.ClassVar[str]
    ENGINE: tp.ClassVar[Engine]
    NAME: tp.ClassVar[str]
    SHORT_NAME: tp.ClassVar[str]

    OLD_J: tp.ClassVar[bool] = False
    REQUIRE_V_WALL: tp.ClassVar[bool] = False
    REQUIRE_SOUND_SHELL_THICKNESS: tp.ClassVar[bool] = False
    #: Whether the engine computes the frequencies with $f_{\ast,0}$ and therefore supports ``f_star0_factor``
    SUPPORTS_F_STAR0_FACTOR: tp.ClassVar[bool] = False

    #: Efficiency of producing bulk kinetic energy relative to a single bubble.
    #: Used by :py:class:`ptplot.science.spectrum.PowerSpectrumDBPL2024`.
    K_EFFICIENCY: tp.ClassVar[float] = 1.

    def __init__(
            self,
            # Primary parameters
            v_wall: float | None = None,
            alpha: float | None = None,
            beta_tilde: float | None = None,
            ubarf: float | None = None,
            r_star: float | None = None,
            T_star: float = DEFAULT_T_STAR,
            g_star: float = DEFAULT_G_STAR,
            # Additional parameters
            adiabatic_index: float = DEFAULT_ADIABATIC_INDEX,
            cs: float = CS0,
            nu_gdh2024: float = DEFAULT_NU_GDH2024,
            f_star0_factor: float = 1.,
            # Switches
            legacy_nucleation_cs_max: bool = False,
            parallel: bool = False):
        r"""
        Create a power spectrum.

        :param T_star: $T_*$, transition temperature
        :param g_star: $g_*$, degrees of freedom
        :param v_wall: $v_\text{wall}$, wall velocity
        :param alpha: $\alpha$, phase transition strength
        :param beta_tilde: $\frac{\beta}{H}$, Inverse phase transition duration relative to $H_*$
        :param ubarf: $\bar{U}_f$, RMS fluid velocity
        :param r_star: $r_*$, typical bubble radius
        :param adiabatic_index: $\Gamma$, mean adiabatic index
        :param cs: $c_s$, sound speed. Used in this base class for:
            1) validation of sound shell thickness,
            2) $\alpha \leftrightarrow \bar{U}_\text{f}$ conversion,
            which uses :py:func:`pttools.bubble.energy_budget.kappa_v_approx`,
            where it's used to determine the solution type and Chapman-Jouguet speed.
            3) $\tilde{\beta} \leftrightarrow r_*$ conversion if ``legacy_nucleation_cs_max`` is enabled
        :param nu_gdh2024: $\nu_\text{gdh2024}$ of :giombi_2024_cs:`\ ` eq. 2.11
        :param f_star0_factor: Correction factor for $f_{\ast,0}$ of :py:func:`pttools.omgw0.freq.f_star0`,
            which converts the frequencies at the time of GW production to frequencies today.
            This is for comparisons with reference values that were computed with a different $f_{\ast,0}$,
            and is supported only by the engines that use $f_{\ast,0}$, see :py:attr:`SUPPORTS_F_STAR0_FACTOR`.
        :param legacy_nucleation_cs_max:
            Use legacy $\max(v_{\text{wall}}, c_s)$ in $\tilde{\beta} \leftrightarrow r_*$ conversion
        :param parallel: Enable parallel processing for this spectrum if the engine supports it.
            This should be disabled when generating multiple spectra in parallel.
        :raises ValueError: If a parameter is invalid
        """
        if f_star0_factor != 1 and not self.SUPPORTS_F_STAR0_FACTOR:
            raise ValueError(f"The engine {self.ENGINE} does not support f_star0_factor. Got {f_star0_factor}.")
        if g_star is None or np.isnan(g_star):
            raise ValueError(f"Invalid g_star={g_star}")
        if T_star is None or np.isnan(T_star):
            raise ValueError(f"Invalid T_star={T_star}")

        #: Unique identifier of the spectrum for exporting
        self.id: str = uuid.uuid4().hex
        #: Frequencies $f$ of the last computed spectrum, see :py:meth:`power_spectrum`
        self.last_f: FloatArr1D | None = None
        #: $\Omega_{\text{gw},0} h^2$ of the last computed spectrum
        self.last_omgw0_h2: FloatArr1D | None = None
        #: SNR of the last computed spectrum
        self.last_snr: float | None = None

        # Parameters that are guaranteed to be set
        #: $\Gamma$, mean adiabatic index
        self.adiabatic_index: float = adiabatic_index
        #: $c_s$, speed of sound
        self.cs: float = cs
        #: Correction factor for $f_{\ast,0}$
        self.f_star0_factor: float = f_star0_factor
        #: $g_*$, degrees of freedom
        self.g_star: float = g_star
        #: $N_\text{sh}$, number of shock formation times
        self.N_sh: float = DEFAULT_N_SH
        #: $\nu_\text{gdh2024}$ of :giombi_2024_cs:`\ ` eq. 2.11
        self.nu_gdh2024: float = nu_gdh2024
        #: Whether parallel processing is enabled
        self.parallel: bool = parallel
        #: $T_*$, transition temperature
        self.T_star: float = T_star

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

    def F_gw0_h2(  # noqa: D102
            self,
            ge0_photon: FloatOrArr = GE0_PHOTON,
            gs0: FloatOrArr = GS0,
            gs_star: FloatOrArr | None = None,
            om_gamma0_h2: FloatOrArr = OMEGA_PHOTON_H2) -> FloatOrArr:
        return F_gw0_h2(ge_star=self.g_star, ge0_photon=ge0_photon, gs0=gs0, gs_star=gs_star, om_gamma0_h2=om_gamma0_h2)

    def h_star(self) -> float:
        r"""$h_*$, inverse Hubble time at GW production, redshifted to today.

        :caprini_2016:`\ ` eq. 11
        """
        return 16.5e-6 * (self.T_star / 100) * (self.g_star / 100) ** (1 / 6)

    @property
    def H_star_eta_sh(self) -> float:  # noqa: D102
        return H_star_eta_sh(r_star=self.r_star, ubarf=self.ubarf)

    @property
    def H_star_eta_v(self) -> float:  # noqa: D102
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

    def record(self, extractor: Extractor) -> Record | None:
        """Record of the spectrum computed by the last call of :py:meth:`power_spectrum` for exporting it.

        The record can be added to a :py:class:`pttools.export.exporter.Exporter`.
        The spectrum is stored in the table :py:attr:`TABLE` with the fields
        of :py:mod:`ptplot.science.spectrum.export`.

        :param extractor: Extractor of the exporter, which defines the fields to be extracted,
            see :py:attr:`pttools.export.exporter.Exporter.extractor`
        :return: Record of the spectrum, or None if the engine does not support exporting
            or if no spectrum has been computed
        """
        if self.TABLE is None or self.last_f is None:
            return None
        return extractor.extract(self)

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

    def snr_and_store(
            self,
            f: FloatArr1D,
            power_spectrum: FloatArr1D,
            noise: Noise | None) -> tuple[FloatArr1D, float]:
        r"""Compute the SNR of a computed power spectrum, and store both for exporting.

        This should be called at the end of :py:meth:`power_spectrum`.

        :param f: Frequencies $f$ of the power spectrum
        :param power_spectrum: GW power spectrum $\Omega_\text{gw} h^2$
        :param noise: Noise curve to compare against. The default noise curve is used, if one is not given.
        :return: The power spectrum and its SNR
        """
        snr = self.snr(f=f, power_spectrum=power_spectrum, noise=resolve_noise(noise))
        self.last_f = f
        self.last_omgw0_h2 = power_spectrum
        self.last_snr = snr
        return power_spectrum, snr

    # The docstring is copied from PTtools with copy_docstrings() at the end of this file.
    def source_lifetime_factor(self) -> float:  # noqa: D102
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
        r"""Validate $\alpha$ and $\bar{U}_\text{f}$, and compute the one that is not given.

        Exactly two of $v_\text{wall}$, $\alpha$ and $\bar{U}_\text{f}$ must be given.

        :param alpha: $\alpha$, phase transition strength
        :param ubarf: $\bar{U}_f$, RMS fluid velocity
        :param v_wall: $v_\text{wall}$, wall velocity
        :param adiabatic_index: $\Gamma$, mean adiabatic index
        :param cs: $c_s$, sound speed
        :param v_cj: $v_\text{CJ}$, Chapman-Jouguet speed
        :param model: Equation of state model of PTtools
        :return: $\alpha$ and $\bar{U}_f$.
            $\alpha$ is nan if it cannot be computed from $\bar{U}_f$.
        :raises ValueError: If not exactly two of the parameters are given
        """
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

    def validate_v_wall(self, v_wall: float | None, cs: float = CS0) -> float | None:
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
    PowerSpectrum.H_star_eta_v: H_star_eta_v,
    PowerSpectrum.source_lifetime_factor: source_lifetime_factor
}, without_params=True)
