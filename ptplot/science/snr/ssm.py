"""SNR utilities for the Sound Shell Model."""

import dataclasses
import logging

import numpy as np
from pttools.bubble import Bubble
from pttools.export import Extractor, Record
from pttools.models import Model

from ptplot.science import const
from ptplot.science import type_hints as th
from ptplot.science.noise import Noise, resolve_noise
from ptplot.science.snr.point import extract_record
from ptplot.science.spectrum.ssm import BAG, PowerSpectrumSSM

logger: logging.Logger = logging.getLogger(__name__)


@dataclasses.dataclass(slots=True)
class SNRColumn:
    r"""A column of an SNR grid computed with the Sound Shell Model.

    This is a class instead of a tuple,
    so that :py:func:`pttools.speedup.parallel.run_parallel` can store it in an object array as is.
    """

    #: SNR values for each $y$
    snr: th.FloatArr1D
    #: $\mathcal{H}_* \eta_\text{sh}$ for each $y$
    shock_times: th.FloatArr1D
    #: Records of the computed spectra for exporting, if an extractor was given
    records: list[Record] = dataclasses.field(default_factory=list)


def snr_column_ssm(
        x: th.FloatOrArr1D,
        y: th.FloatArr1D,
        v_wall: float,
        T_star: float,
        g_star: float,
        ubarf_rstar: bool = False,
        adiabatic_index: float = const.DEFAULT_ADIABATIC_INDEX,
        model: Model = BAG,
        noise: Noise | None = None,
        f_star0_factor: float = 1.,
        parallel: bool = False,
        legacy_nucleation_cs_max: bool = False,
        extractor: Extractor | None = None) -> SNRColumn:
    r"""Compute a column of an SNR grid with the Sound Shell Model.

    The fluid shell is computed only once for the column, as $x$ is the same for all its points.
    If the computation of a point fails, its values are NaN, as in :py:func:`ptplot.science.snr.point.snr_point`,
    and if the fluid shell cannot be created, all the values of the column are NaN.
    The errors are logged.

    :param x: $\alpha$ or $\bar{U}_f$, a scalar
    :param y: $\tilde{\beta}$ or $r_*$ values of the column
    :param v_wall: $v_\text{wall}$, wall velocity
    :param T_star: $T_*$, temperature at which the GWs were produced
    :param g_star: $g_*$, degrees of freedom
    :param ubarf_rstar: Whether $x$ and $y$ are $\bar{U}_f$ and $r_*$ instead of $\alpha$ and $\tilde{\beta}$
    :param adiabatic_index: $\Gamma$, mean adiabatic index
    :param model: Equation of state model of PTtools
    :param noise: Which noise curve to use
    :param f_star0_factor: Correction factor for $f_{\ast,0}$,
        see :py:class:`~ptplot.science.spectrum.base.PowerSpectrum`
    :param parallel: Enable parallel processing for the spectra
    :param legacy_nucleation_cs_max:
        Use legacy $\max(v_{\text{wall}}, c_s)$ in $\tilde{\beta} \leftrightarrow r_*$ conversion
    :param extractor: Extractor of a :py:class:`pttools.export.exporter.Exporter`.
        If given, the fields of the spectra are extracted for exporting.
        The extraction is done here, so that only the extracted fields have to be sent between the processes
        when the columns are computed in parallel.
    :return: SNR values, $\mathcal{H}_* \eta_\text{sh}$ values and the records of the spectra
    :raises ValueError: If $x$ is not a scalar
    """
    noise = resolve_noise(noise)
    x_value: float
    if isinstance(x, np.ndarray):
        if x.size != 1:
            raise ValueError(f"x (alpha_n or ubarf) must be a scalar. Got a {x.shape} array.")
        x_value = x.item()
    else:
        x_value = x

    x_name = "ubarf" if ubarf_rstar else "alpha"
    y_name = "r_star" if ubarf_rstar else "beta_tilde"
    column = SNRColumn(snr=np.full(y.size, np.nan), shock_times=np.full(y.size, np.nan))
    try:
        alpha_n, _ubarf = PowerSpectrumSSM.validate_alpha_ubarf_static(
            alpha=None if ubarf_rstar else x_value,
            ubarf=x_value if ubarf_rstar else None,
            v_wall=v_wall,
            adiabatic_index=adiabatic_index,
            cs=const.CS0,
            model=model
        )
        bubble = Bubble(model=model, v_wall=v_wall, alpha_n=alpha_n)
    except Exception as exc:
        logger.exception(
            "Failed to create the fluid shell for the SNR column with %s=%s, v_wall=%s",
            x_name, x_value, v_wall,
            exc_info=exc
        )
        return column

    for i, y_i in enumerate(y):
        try:
            spectrum = PowerSpectrumSSM(
                alpha=None if ubarf_rstar else x_value,
                ubarf=x_value if ubarf_rstar else None,
                beta_tilde=None if ubarf_rstar else y_i,
                r_star=y_i if ubarf_rstar else None,
                T_star=T_star,
                g_star=g_star,
                v_wall=v_wall,
                adiabatic_index=adiabatic_index,
                model=model,
                bubble=bubble,
                f_star0_factor=f_star0_factor,
                parallel=parallel,
                legacy_nucleation_cs_max=legacy_nucleation_cs_max
            )
            # Error logging is handled in this function
            _power_spectrum, snr = spectrum.power_spectrum(noise.f, noise=noise, log_errors=False)
            shock_time = spectrum.H_star_eta_sh
        except Exception as exc:
            logger.exception(
                "Failed to compute SNR for %s=%s, %s=%s, T_star=%s, g_star=%s, v_wall=%s, noise=%s, engine=SSM",
                x_name, x_value, y_name, y_i, T_star, g_star, v_wall, noise,
                exc_info=exc
            )
            continue
        column.snr[i] = snr
        column.shock_times[i] = shock_time
        if extractor is not None:
            record = extract_record(spectrum, extractor)
            if record is not None:
                column.records.append(record)
    return column
