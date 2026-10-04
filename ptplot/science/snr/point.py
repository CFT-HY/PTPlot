"""Signal-to-noise ratio calculations for gravitational wave spectra."""

from collections.abc import Iterable
import logging
import typing as tp

import numpy as np
from pttools.export import Exporter, Extractor, Record

from ptplot.science import const
from ptplot.science.noise import Noise, resolve_noise
from ptplot.science.spectrum.base import PowerSpectrum
from ptplot.science.spectrum.create import power_spectrum
from ptplot.science.spectrum.engine import Engine

logger: logging.Logger = logging.getLogger(__name__)


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
        parallel: bool = True,
        legacy_nucleation_cs_max: bool = False,
        extractor: Extractor | None = None) -> tuple[float, float, Record | None]:
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
    :param parallel: Enable parallel processing for the spectrum if the engine supports it
    :param legacy_nucleation_cs_max:
        Use legacy $\max(v_{\text{wall}}, c_s)$ in $\tilde{\beta} \leftrightarrow r_*$ conversion
    :param extractor: Extractor of a :py:class:`pttools.export.exporter.Exporter`.
        If given, the fields of the spectrum are extracted for exporting,
        see :py:meth:`ptplot.science.spectrum.base.PowerSpectrum.record`.
    :return: SNR, $\mathcal{H}_* \eta_\text{sh}$ and the record of the spectrum.
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
            parallel=parallel,
            legacy_nucleation_cs_max=legacy_nucleation_cs_max,
            **kwargs
        )
        # Error logging is handled in this function
        _power_spectrum, snr = spectrum.power_spectrum(noise.f, noise=noise, log_errors=False)
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
        return np.nan, np.nan, None
    return snr, shock_time, None if extractor is None else extract_record(spectrum, extractor)


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
