"""Sound Shell Model (SSM) power spectrum."""

# from functools import lru_cache
import logging
import typing as tp

import numpy as np
from pttools.bubble import DEFAULT_NU_GDH2024, Bubble, SolutionType
from pttools.export import Extractor, Record
from pttools.models import BagModel, Model
from pttools.omgw0 import GE0_PHOTON, GS0, Spectrum, Suppression, SuppressionMethod, signal_to_noise_ratio
from pttools.ssm.nucleation import DEFAULT_NUC_TYPE, NucType
from pttools.ssm.settings import SSMSettings
from pttools.ssm.suppression import DEFAULT_SUPPRESSION

from ptplot.science.const import DEFAULT_ADIABATIC_INDEX, DEFAULT_G_STAR, DEFAULT_T_STAR, OMEGA_PHOTON_H2
from ptplot.science.noise import Noise, resolve_noise
from ptplot.science.spectrum.base import PowerSpectrum
from ptplot.science.spectrum.engine import Engine
from ptplot.science.type_hints import FloatArr1D

BAG: BagModel = BagModel(alpha_n_min=0.0001)

logger: logging.Logger = logging.getLogger(__name__)


class PowerSpectrumSSM(PowerSpectrum):
    """Sound Shell Model (SSM) power spectrum.

    Uses PTtools to compute the fluid velocity profile and the resulting GW power spectrum.
    """

    COLOR = "blue"
    LINESTYLE: tp.ClassVar[str] = "--"
    ENGINE: tp.ClassVar[Engine] = Engine.SSM
    NAME: tp.ClassVar[str] = "Sound Shell Model"
    SHORT_NAME: tp.ClassVar[str] = "SSM"

    REQUIRE_V_WALL = True
    SUPPORTS_F_STAR0_FACTOR = True

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
            f_star0_factor: float = 1.,
            # Switches
            legacy_nucleation_cs_max: bool = False,
            parallel: bool = False,
            model: Model | None = None,
            bubble: Bubble | None = None,
            # Precomputation
            z: FloatArr1D | None = None,
            settings: SSMSettings | None = None,
            suppression: Suppression = DEFAULT_SUPPRESSION,
            suppression_method: SuppressionMethod = SuppressionMethod.EXT_CONSTANT):
        r"""Create an SSM power spectrum.

        :param model: Equation of state model of PTtools.
            Defaults to that of the fluid shell if one is given, and otherwise to the bag model.
        :param bubble: Precomputed fluid shell, e.g. for reusing it for multiple spectra.
            It must have the same $v_\text{wall}$, $\alpha$ and model as this spectrum.
            If not given, it is computed from these.
        :param z: $z = k R_*$ array. If given, the PTtools spectrum is computed for it immediately,
            and stored as :py:attr:`precomputed`. :py:meth:`power_spectrum` then interpolates it
            for the frequencies that are within its range, and :py:meth:`with_params` reuses it.
            See :py:meth:`pttools.omgw0.spectrum.Spectrum.z_covering`
            for creating a $z$ array that covers the given frequencies.
        :param settings: Accuracy settings of the PTtools spectra,
            defaults to :py:class:`pttools.ssm.settings.SSMSettings`.
            The lookup arrays span the range of the $z$ array.
            Therefore, for a $z$ array that spans a wider range than the frequencies,
            ``n_z_lookup`` should be increased with
            :py:meth:`pttools.omgw0.spectrum.Spectrum.n_z_lookup_covering` to retain the accuracy.
        :param suppression: Suppression data of the precomputed spectrum
        :param suppression_method: Suppression method of the precomputed spectrum
        :raises ValueError: If the fluid shell does not match the parameters of this spectrum
        """
        # These are stored so that with_params() can give the same parameters to the new spectrum.
        self._alpha_given: float | None = alpha
        self._ubarf_given: float | None = ubarf
        self._legacy_nucleation_cs_max: bool = legacy_nucleation_cs_max
        if model is None:
            model = BAG if bubble is None else bubble.model
        elif bubble is not None and bubble.model is not model:
            raise ValueError("The fluid shell must have the same model as the power spectrum.")
        self.model: Model = model
        # Compute the bubble early if possible so that it can be used for nucleation suppression.
        self._bubble: Bubble | None = bubble if bubble is not None \
            else None if v_wall is None or alpha is None \
            else Bubble(model=model, v_wall=v_wall, alpha_n=alpha)
        super().__init__(
            beta_tilde=beta_tilde,
            T_star=T_star,
            g_star=g_star,
            v_wall=v_wall,
            # cs=TODO
            adiabatic_index=adiabatic_index,
            alpha=alpha,
            f_star0_factor=f_star0_factor,
            nu_gdh2024=DEFAULT_NU_GDH2024 if self._bubble is None else self._bubble.nu_gdh2024,
            r_star=r_star,
            ubarf=ubarf,
            parallel=parallel,
            legacy_nucleation_cs_max=legacy_nucleation_cs_max
        )
        if self.v_wall is None or np.isnan(self.v_wall):
            raise ValueError(f"Sound Shell Model requires v_wall to be set. Got v_wall={v_wall}.")
        if bubble is not None and not (
                np.isclose(bubble.v_wall, self.v_wall) and np.isclose(bubble.alpha_n, self.alpha)):
            raise ValueError(
                "The fluid shell must have the same v_wall and alpha as the power spectrum. "
                f"Got v_wall={self.v_wall}, alpha={self.alpha} for the spectrum and "
                f"v_wall={bubble.v_wall}, alpha_n={bubble.alpha_n} for the fluid shell."
            )

        self.bubble: Bubble = Bubble(model=self.model, v_wall=self.v_wall, alpha_n=self.alpha) \
            if self._bubble is None else self._bubble
        #: The PTtools spectrum computed by the last successful call of :py:meth:`power_spectrum`
        self.spectrum: Spectrum | None = None
        #: Accuracy settings of the PTtools spectra
        self.settings: SSMSettings = SSMSettings() if settings is None else settings
        #: Suppression data of :py:attr:`precomputed`
        self.suppression: Suppression = suppression
        #: Suppression method of :py:attr:`precomputed`
        self.suppression_method: SuppressionMethod = suppression_method
        #: The PTtools spectrum precomputed for the $z$ array given to the constructor
        self.precomputed: Spectrum | None = None if z is None else self._spectrum(
            z=z, suppression=suppression, suppression_method=suppression_method)

    def _spectrum(
            self,
            suppression: Suppression,
            suppression_method: SuppressionMethod,
            f: FloatArr1D | None = None,
            z: FloatArr1D | None = None,
            nuc_type: NucType = DEFAULT_NUC_TYPE) -> Spectrum:
        """Compute the PTtools spectrum for either the frequencies ``f`` or the $z$ array."""
        return Spectrum(
            bubble=self.bubble,
            f=None if f is None else f / self.f_star0_factor,
            y=z,
            beta_tilde=self.beta_tilde_given,
            g_star=self.g_star,
            r_star=self.r_star_given,
            T_star=self.T_star,
            nuc_type=nuc_type,
            # r_* is computed from beta_tilde in the same way for all nucleation types, see power_spectrum().
            allow_beta_tilde_for_simultaneous=True,
            suppression=suppression,
            suppression_method=suppression_method,
            parallel=self.parallel,
            **self.settings.spectrum_kwargs()
        )

    def covers(self, f: FloatArr1D, rtol: float = 1e-9) -> bool:
        """Whether the frequencies are within the $z$ range of the precomputed spectrum.

        :param f: Frequencies $f$
        :param rtol: Relative tolerance for the endpoints of the range
        :return: True if the spectrum has been precomputed and ``f`` is within its range
        """
        if self.precomputed is None:
            return False
        return self.precomputed.covers(self.precomputed.z_from_f(f / self.f_star0_factor), rtol=rtol)

    def interpolated_spectrum(self, f: FloatArr1D) -> Spectrum:
        r"""The precomputed spectrum interpolated to the frequencies ``f``.

        The result is a PTtools spectrum that has been given the frequencies ``f``,
        and can therefore be exported in the same way as a spectrum computed for them,
        to the table :py:attr:`pttools.export.records.Table.SPECTRA_F`.
        It is created with :py:meth:`pttools.omgw0.spectrum.Spectrum.with_params`,
        which interpolates the precomputed spectrum to $z(f)$.

        :param f: Frequencies $f$, which must be within the range of the precomputed spectrum, see :py:meth:`covers`
        :return: The interpolated spectrum
        :raises ValueError: If the spectrum has not been precomputed, or if ``f`` is not within its range
        """
        if self.precomputed is None:
            raise ValueError("The spectrum has not been precomputed.")
        return self.precomputed.with_params(f=f / self.f_star0_factor)

    @property
    def z_range(self) -> tuple[float, float] | None:
        """The minimum and maximum $z$ of the precomputed spectrum, or None if it has not been precomputed."""
        if self.precomputed is None:
            return None
        return self.precomputed.y.min(), self.precomputed.y.max()

    @property
    def kinetic_energy_fraction(self) -> float:
        """Kinetic energy fraction $K$.

        Computed from the fluid shell using :py:func:`pttools.bubble.thermo.kinetic_energy_fraction`.
        """
        return self.bubble.kinetic_energy_fraction

    def power_spectrum(
            self,
            f: FloatArr1D,
            noise: Noise | None = None,
            log_errors: bool = True,
            ge0_photon: float = GE0_PHOTON,
            gs0: float = GS0,
            om_gamma0_h2: float = OMEGA_PHOTON_H2,
            suppression: Suppression = DEFAULT_SUPPRESSION,
            suppression_method: SuppressionMethod = SuppressionMethod.EXT_CONSTANT,
            nuc_type: NucType = DEFAULT_NUC_TYPE) \
            -> tuple[FloatArr1D, float]:
        r"""Power spectrum $\mathcal{P}_\text{gw} h^2$ from the Sound Shell Model, and its SNR.

        The bubble lifetime distribution is that of the nucleation type ``nuc_type``,
        see :py:class:`pttools.ssm.nucleation.NucType`.
        It does not currently affect $r_*$, which is computed from $\tilde{\beta}$
        in the same way for all nucleation types.

        The SNR is computed by :py:meth:`PowerSpectrum.snr` on the frequencies ``f``,
        in the same way as :py:meth:`pttools.omgw0.spectrum.Spectrum.snr`.

        The $f \to z$ conversion of PTtools uses $f_{\ast,0}$ of :py:func:`pttools.omgw0.freq.f_star0`.
        To apply :py:attr:`f_star0_factor`, the PTtools spectrum is given the frequencies ``f / f_star0_factor``,
        which correspond to the same $z$ values as ``f`` with the corrected $f_{\ast,0}$.
        Therefore, if ``f_star0_factor`` is not 1,
        the frequencies of :py:attr:`spectrum` differ from ``f`` by this factor.

        .. note::
           When $\frac{\beta}{H_*}$ is given instead of $r_*$,
           PTtools computes $r_*$ with :py:func:`pttools.ssm.nucleation.r_star`,
           which differs from :py:func:`ptplot.science.utils.R_star` that is used here for the $f \to z$
           conversion. The frequencies of the returned spectrum are therefore those given in ``f``,
           whereas the SNR is integrated over the frequencies that PTtools assigns to the same $z$ values.

        If the spectrum has been precomputed with the same suppression settings and nucleation type
        (see :py:attr:`precomputed`), and ``f`` is within its $z$ range (see :py:meth:`covers`),
        the precomputed spectrum is used instead of computing a new one.
        Then the returned power spectrum is that of :py:meth:`interpolated_spectrum`,
        i.e. the precomputed spectrum is interpolated to ``f`` by PTtools,
        whereas the SNR is computed on the non-interpolated points of the precomputed spectrum
        within the range of ``f``, with the noise evaluated at these points.
        :py:attr:`spectrum` is then set to the interpolated spectrum.
        """
        noise = resolve_noise(noise)
        self.spectrum = None
        try:
            # If the precomputed spectrum can be used
            if self.precomputed is not None \
                    and suppression is self.suppression \
                    and suppression_method == self.suppression_method \
                    and nuc_type == self.precomputed.nuc_type \
                    and self.covers(f):
                return self._power_spectrum_precomputed(
                    f=f, noise=noise, ge0_photon=ge0_photon, gs0=gs0, om_gamma0_h2=om_gamma0_h2)
            spectrum = self._spectrum(
                f=f, suppression=suppression, suppression_method=suppression_method, nuc_type=nuc_type)
            omgw0_h2 = spectrum.omgw0_h2(ge0_photon=ge0_photon, gs0=gs0, om_gamma0_h2=om_gamma0_h2)
            snr = self.snr(f=f, power_spectrum=omgw0_h2, noise=noise)
            self.spectrum = spectrum
            return omgw0_h2, snr
        except Exception as exc:
            if log_errors:
                logger.exception(
                    "Could not create SSM power spectrum with r_star=%s, g_star=%s, Tn=%s, "
                    "f = %.3e - %.3e (%s points)",
                    self.r_star, self.g_star, self.T_star, f.min(), f.max(), f.size,
                    exc_info=exc
                )
            raise exc

    def _power_spectrum_precomputed(
            self,
            f: FloatArr1D,
            noise: Noise,
            ge0_photon: float,
            gs0: float,
            om_gamma0_h2: float) -> tuple[FloatArr1D, float]:
        """Power spectrum interpolated from the precomputed spectrum, and the SNR of its points within ``f``."""
        pre = tp.cast(Spectrum, self.precomputed)
        f_pre = pre.f() * self.f_star0_factor
        omgw0_h2_pre = pre.omgw0_h2(ge0_photon=ge0_photon, gs0=gs0, om_gamma0_h2=om_gamma0_h2)
        spectrum = self.interpolated_spectrum(f)
        omgw0_h2 = spectrum.omgw0_h2(ge0_photon=ge0_photon, gs0=gs0, om_gamma0_h2=om_gamma0_h2)

        in_range = (f_pre >= f.min()) & (f_pre <= f.max())
        if np.count_nonzero(in_range) < 2:  # noqa: PLR2004
            raise ValueError(
                "The precomputed spectrum has fewer than two points within "
                f"f = {f.min():.3e} - {f.max():.3e}. Use a denser z array."
            )
        f_snr = f_pre[in_range]
        snr, _f_noise, _noise = signal_to_noise_ratio(
            f=f_snr,
            signal=omgw0_h2_pre[in_range],
            noise=noise.noise_at(f_snr),
            obs_time=noise.obs_time
        )
        self.spectrum = spectrum
        return omgw0_h2, snr

    def with_params(
            self,
            beta_tilde: float | None = None,
            r_star: float | None = None,
            T_star: float | None = None,
            g_star: float | None = None,
            f_star0_factor: float | None = None,
            parallel: bool | None = None) -> tp.Self:
        r"""Create a new spectrum with different parameters, reusing the fluid shell and the precomputed spectrum.

        The parameters that are not given are taken from this spectrum.
        If either $\tilde{\beta}$ or $r_*$ is given, the other one is not taken from this spectrum.
        The parameters that would change the fluid shell cannot be changed.

        If the spectrum has been precomputed, the precomputed spectrum of the new spectrum is created with
        :py:meth:`pttools.omgw0.spectrum.Spectrum.with_params`, which reuses the computationally heavy part.
        It therefore has the same $z$ array as this spectrum,
        and the frequencies that it covers change when $r_*$, $T_*$, $g_*$ or ``f_star0_factor`` is changed.

        :param beta_tilde: $\tilde{\beta} \equiv \frac{\beta}{H_*}$, nucleation rate parameter
        :param r_star: $r_*$, Hubble-scaled mean bubble spacing
        :param T_star: $T_*$, temperature at which the GWs were produced
        :param g_star: $g_*$, degrees of freedom
        :param f_star0_factor: Correction factor for $f_{\ast,0}$
        :param parallel: Enable parallel processing
        :return: The new spectrum
        """
        if beta_tilde is None and r_star is None:
            beta_tilde = self.beta_tilde_given
            r_star = self.r_star_given
        # z is not given, and therefore creating the object does not precompute its Spectrum.
        spectrum = type(self)(
            v_wall=self.v_wall,
            alpha=self._alpha_given,
            beta_tilde=beta_tilde,
            ubarf=self._ubarf_given,
            r_star=r_star,
            T_star=self.T_star if T_star is None else T_star,
            g_star=self.g_star if g_star is None else g_star,
            adiabatic_index=self.adiabatic_index,
            f_star0_factor=self.f_star0_factor if f_star0_factor is None else f_star0_factor,
            legacy_nucleation_cs_max=self._legacy_nucleation_cs_max,
            parallel=self.parallel if parallel is None else parallel,
            model=self.model,
            bubble=self.bubble,
            settings=self.settings,
            suppression=self.suppression,
            suppression_method=self.suppression_method
        )
        if self.precomputed is not None:
            spectrum.precomputed = self.precomputed.with_params(
                beta_tilde=spectrum.beta_tilde_given,
                r_star=spectrum.r_star_given,
                T_star=spectrum.T_star,
                g_star=spectrum.g_star
            )
        return spectrum

    def record(self, extractor: Extractor) -> Record | None:
        """Record of the PTtools spectrum computed by the last call of :py:meth:`power_spectrum`.

        The spectrum has been given the frequencies $f$, or interpolated to them from the precomputed spectrum
        (see :py:meth:`interpolated_spectrum`), and is therefore stored in the table
        :py:attr:`pttools.export.records.Table.SPECTRA_F`.
        The parameters are those of :py:meth:`PowerSpectrum.record`.
        """
        return None if self.spectrum is None else extractor.extract(self.spectrum)

    def validate_alpha_ubarf(
            self,
            alpha: float | None,
            ubarf: float | None,
            v_wall: float | None,
            adiabatic_index: float,
            cs: float,
            v_cj: float | None = None,
            model: Model | None = None) -> tuple[float, float]:
        r"""Validate $\alpha$ and $\bar{U}_\text{f}$ with the equation of state model of this spectrum.

        The parameters are those of :py:meth:`PowerSpectrum.validate_alpha_ubarf_static`,
        and the model defaults to that of this spectrum.
        """
        return super().validate_alpha_ubarf(
            alpha=alpha,
            ubarf=ubarf,
            v_wall=v_wall,
            adiabatic_index=adiabatic_index,
            cs=cs,
            v_cj=v_cj,
            model=self.model if model is None else model
        )

    def validate_beta_r_star(
            self,
            beta_tilde: float | None,
            r_star: float | None,
            v_wall: float | None,
            xi: FloatArr1D | None = None,
            T: FloatArr1D | None = None,
            sol_type: SolutionType | None = None,
            legacy_cs: float | None = None) -> tuple[float, float]:
        r"""Validate $\tilde{\beta}$ and $r_*$ with the fluid shell, if it has already been computed.

        The parameters are those of :py:meth:`PowerSpectrum.validate_beta_r_star`,
        but $\xi$, $T$ and the solution type default to those of the fluid shell.
        If the fluid shell has not been computed yet, the solution type defaults to a detonation.
        """
        if sol_type is None:
            sol_type = SolutionType.DETON if self._bubble is None else self._bubble.sol_type
        return super().validate_beta_r_star(
            beta_tilde=beta_tilde,
            r_star=r_star,
            v_wall=v_wall,
            xi=self._bubble.xi if xi is None and self._bubble is not None else xi,
            T=tp.cast(FloatArr1D, self._bubble.T) if T is None and self._bubble is not None else T,
            sol_type=sol_type,
            legacy_cs=legacy_cs
        )

# @lru_cache(maxsize=256)
# def bubble(model: Model, v_wall: float, alpha_n: float) -> Bubble:
#     """Caching Bubble generator for speed-up"""
#     return Bubble(model=model, v_wall=v_wall, alpha_n=alpha_n)
