"""Signal-to-noise ratio calculations for gravitational wave spectra."""

from collections.abc import Iterable
import dataclasses
import logging
import math
import typing as tp

import numpy as np
from pttools.export import Exporter, Extractor, Record

from ptplot.science import const
from ptplot.science.noise import Noise, resolve_noise
from ptplot.science.spectrum.base import PowerSpectrum
from ptplot.science.spectrum.create import power_spectrum
from ptplot.science.spectrum.engine import Engine
from ptplot.science.spectrum.ssm import PowerSpectrumSSM, SSMSettings
from ptplot.science.type_hints import FloatArr1D

logger: logging.Logger = logging.getLogger(__name__)

#: Parameters of the power spectra that are stored for each point of an SNR grid, see :py:func:`spectrum_params`
SPECTRUM_PARAMS: tuple[str, ...] = ("alpha", "beta_tilde", "ubarf", "r_star")
#: Additional parameters of the power spectra of the Sound Shell Model, see :py:func:`spectrum_params`
SPECTRUM_PARAMS_SSM: tuple[str, ...] = ("ubarf_bubble", "ubarf_spectrum")


@dataclasses.dataclass(frozen=True, slots=True)
class SNRPointSpectrum:
    """The power spectrum of a single point of an SNR grid, its parameters, and its record for exporting.

    This is a class instead of a tuple,
    so that :py:func:`pttools.speedup.parallel.run_parallel` can store it in an object array as is.
    """

    #: Power spectrum $h^2 \Omega_\text{gw,0}$ at the frequencies of the noise curve, NaN if the computation failed
    omgw0_h2: FloatArr1D
    #: Parameters of the spectrum, see :py:func:`spectrum_params`. Empty if the computation failed.
    params: dict[str, float] = dataclasses.field(default_factory=dict)
    #: Record of the spectrum for exporting, if an extractor was given and the extraction succeeded
    record: Record | None = None


def snr_point(
        x: float,
        y: float,
        T_star: float,
        g_star: float,
        v_wall: float,
        noise: Noise | None,
        engine: Engine,
        adiabatic_index: float = const.DEFAULT_ADIABATIC_INDEX,
        ubarf_rstar: bool = False,
        f_star0_factor: float = 1.,
        parallel: bool = True,
        legacy_nucleation_cs_max: bool = False,
        extractor: Extractor | None = None,
        ssm_settings: SSMSettings | None = None) -> tuple[float, float, SNRPointSpectrum]:
    r"""Compute the SNR value of a single point in the parameter space.

    :param x: $\alpha$ or $\bar{U}_f$
    :param y: $\tilde{\beta}$ or $r_*$
    :param T_star: $T_*$, temperature at which the GWs were produced
    :param g_star: $g_*$, degrees of freedom
    :param v_wall: $v_\text{wall}$, wall velocity
    :param noise: Which noise curve to use
    :param engine: Which power spectrum engine to use
    :param adiabatic_index: $\Gamma$, mean adiabatic index
    :param ubarf_rstar: Whether $x$ and $y$ are $\bar{U}_f$ and $r_*$ instead of $\alpha$ and $\tilde{\beta}$
    :param f_star0_factor: Correction factor for $f_{\ast,0}$,
        see :py:class:`~ptplot.science.spectrum.base.PowerSpectrum`
    :param parallel: Enable parallel processing for the spectrum if the engine supports it
    :param legacy_nucleation_cs_max:
        Use legacy $\max(v_{\text{wall}}, c_s)$ in $\tilde{\beta} \leftrightarrow r_*$ conversion
    :param extractor: Extractor of a :py:class:`pttools.export.exporter.Exporter`.
        If given, the fields of the spectrum are extracted for exporting,
        see :py:meth:`ptplot.science.spectrum.base.PowerSpectrum.record`.
    :param ssm_settings: Accuracy settings of the PTtools spectra of the SSM engine
    :return: SNR, $\mathcal{H}_* \eta_\text{sh}$, and the power spectrum $h^2 \Omega_\text{gw,0}$
        at the frequencies of the noise curve with the record of the spectrum.
        If the computation fails, the values and the spectrum are NaN.
        The record is None if the extractor is not given, if the engine does not support exporting,
        or if the computation or the extraction failed.
    """
    noise = resolve_noise(noise)
    kwargs: dict[str, tp.Any] = {"ubarf": x, "r_star": y} if ubarf_rstar \
        else {"alpha": x, "beta_tilde": y}
    try:
        spectrum = power_spectrum(
            T_star=T_star,
            g_star=g_star,
            v_wall=v_wall,
            adiabatic_index=adiabatic_index,
            engine=engine,
            f_star0_factor=f_star0_factor,
            parallel=parallel,
            legacy_nucleation_cs_max=legacy_nucleation_cs_max,
            ssm_settings=ssm_settings,
            **kwargs
        )
        # Error logging is handled in this function
        omgw0_h2, snr = spectrum.power_spectrum(noise.f, noise=noise, log_errors=False)
        shock_time = spectrum.H_star_eta_sh
    except Exception as exc:
        logger.exception(
            "Failed to compute SNR for %s=%s, %s=%s, T_star=%s, g_star=%s, v_wall=%s, "
            "noise=%s, engine=%s, adiabatic_index=%s",
            "ubarf" if ubarf_rstar else "alpha", x,
            "r_star" if ubarf_rstar else "beta_tilde", y,
            T_star, g_star, v_wall, noise, engine, adiabatic_index,
            exc_info=exc
        )
        return np.nan, np.nan, SNRPointSpectrum(omgw0_h2=np.full(noise.f.size, np.nan))
    return snr, shock_time, SNRPointSpectrum(
        omgw0_h2=omgw0_h2,
        params=spectrum_params(spectrum),
        record=None if extractor is None else extract_record(spectrum, extractor)
    )


def extract_record(spectrum: PowerSpectrum, extractor: Extractor) -> Record | None:
    """Extract the record of a computed spectrum for exporting, and log the errors instead of raising them.

    Exporting is an addition to the SNR computation, and therefore a failure to extract the fields
    of a single spectrum should not prevent the computation of the SNR grid it belongs to.

    :param spectrum: Power spectrum,
        whose :py:meth:`~ptplot.science.spectrum.base.PowerSpectrum.power_spectrum` has been called
    :param extractor: Extractor of a :py:class:`pttools.export.exporter.Exporter`
    :return: Record of the spectrum, or None if the engine does not support exporting or if the extraction failed
    """
    try:
        return spectrum.record(extractor)
    except Exception as exc:
        logger.exception(
            "Failed to extract the fields of the %s spectrum with v_wall=%s, alpha=%s, r_star=%s for exporting",
            spectrum.ENGINE, spectrum.v_wall, spectrum.alpha, spectrum.r_star,
            exc_info=exc
        )
        return None


def param_names(engine: Engine) -> tuple[str, ...]:
    """Names of the parameters that :py:func:`spectrum_params` returns for the spectra of an engine.

    :param engine: Power spectrum engine
    :return: :py:data:`SPECTRUM_PARAMS`, and for the SSM engine also :py:data:`SPECTRUM_PARAMS_SSM`
    """
    return SPECTRUM_PARAMS + SPECTRUM_PARAMS_SSM if engine == Engine.SSM else SPECTRUM_PARAMS


def spectrum_params(spectrum: PowerSpectrum) -> dict[str, float]:
    r"""Parameters of a computed power spectrum, as they were computed when the spectrum was created.

    The parameters are $\alpha$, $\tilde{\beta}$, $\bar{U}_f$ and $r_*$
    (see :py:class:`~ptplot.science.spectrum.base.PowerSpectrum`).
    For the Sound Shell Model, they include also ``ubarf_bubble``,
    $\bar{U}_f$ of the fluid shell (:py:attr:`pttools.bubble.bubble.Bubble.ubarf`),
    and ``ubarf_spectrum``, $\sqrt{\bar{U}_f^2}$ of the PTtools spectrum
    (see :py:attr:`pttools.ssm.spectrum.SSMSpectrum.ubarf`).
    The latter is NaN if the PTtools spectrum has not been computed.

    :param spectrum: Power spectrum, whose
        :py:meth:`~ptplot.science.spectrum.base.PowerSpectrum.power_spectrum` has been called
    :return: Parameters by the names of :py:func:`param_names`
    """
    params = {
        "alpha": spectrum.alpha,
        "beta_tilde": spectrum.beta_tilde,
        "ubarf": spectrum.ubarf,
        "r_star": spectrum.r_star,
    }
    if isinstance(spectrum, PowerSpectrumSSM):
        params["ubarf_bubble"] = float(spectrum.bubble.ubarf)
        params["ubarf_spectrum"] = np.nan if spectrum.spectrum is None else math.sqrt(spectrum.spectrum.ubarf2)
    return params


def export_records(exporter: Exporter, records: Iterable[Record | None]) -> None:
    """Add the records of computed spectra to an exporter, and log the errors instead of raising them.

    As with :py:func:`extract_record`, a failure to export the spectra should not discard the computed SNR values.
    If writing to the file has failed, the exporter does not accept more records,
    and therefore each later call logs an error.

    :param exporter: Exporter to which the records are added
    :param records: Records of the spectra. The None values, i.e. the spectra that were not extracted, are skipped.
    """
    try:
        exporter.add_many(record for record in records if record is not None)
    except Exception as exc:
        logger.exception("Failed to export the spectra to %s", exporter.path, exc_info=exc)
