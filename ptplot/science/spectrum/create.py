"""Utilities for creating power spectra."""

import numpy as np
from pttools.models import ConstCSModel, Model

from ptplot.science.const import CS0_2, DEFAULT_ADIABATIC_INDEX, DEFAULT_G_STAR, DEFAULT_T_STAR
from ptplot.science.spectrum.base import PowerSpectrum
from ptplot.science.spectrum.engine import ENGINE_SPECTRUM_CLASSES, Engine
from ptplot.science.spectrum.ssm import BAG, PowerSpectrumSSM, SSMSettings


def power_spectrum(
        v_wall: float | None = None,
        alpha: float | None = None,
        beta_tilde: float | None = None,
        ubarf: float | None = None,
        r_star: float | None = None,
        T_star: float = DEFAULT_T_STAR,
        g_star: float = DEFAULT_G_STAR,
        adiabatic_index: float = DEFAULT_ADIABATIC_INDEX,
        engine: Engine = Engine.DEFAULT,
        css2: float | None = CS0_2,
        csb2: float | None = CS0_2,
        model: Model = BAG,
        f_star0_factor: float = 1.,
        parallel: bool = True,
        legacy_nucleation_cs_max: bool = False,
        cache: bool = False,
        ssm_settings: SSMSettings | None = None) -> PowerSpectrum:
    r"""Create a power spectrum object from the given parameters.

    :param css2: $c_{s,s}^2$, sound speed squared in the symmetric phase, for the SSM, see :py:func:`ssm_model`
    :param csb2: $c_{s,b}^2$, sound speed squared in the broken phase, for the SSM, see :py:func:`ssm_model`
    :param model: Equation of state model for the SSM, see :py:func:`ssm_model`
    :param f_star0_factor: Correction factor for $f_{\ast,0}$,
        see :py:class:`~ptplot.science.spectrum.base.PowerSpectrum`
    :param cache: Get the spectrum, and the model created by :py:func:`ssm_model`, from the cache
        with :py:meth:`pttools.utils.cache.Cacheable.cached`, creating them if necessary.
        As the cached spectra are shared, they should not be modified.
        They also store the results of their last call of
        :py:meth:`~ptplot.science.spectrum.base.PowerSpectrum.power_spectrum`,
        which may therefore have been made elsewhere, e.g. for
        :py:meth:`~ptplot.science.spectrum.base.PowerSpectrum.record`.
    :param ssm_settings: Accuracy settings of the PTtools spectra of the SSM engine
    """
    if engine is None or not engine:
        engine = Engine.DEFAULT
    if engine not in ENGINE_SPECTRUM_CLASSES:
        raise ValueError(f"Invalid engine: {engine}")

    # SSM requires additional arguments
    if engine == Engine.SSM:
        model = ssm_model(css2=css2, csb2=csb2, model=model, cache=cache)
        return (PowerSpectrumSSM.cached if cache else PowerSpectrumSSM)(
            beta_tilde=beta_tilde, T_star=T_star, g_star=g_star,
            v_wall=v_wall, adiabatic_index=adiabatic_index,
            alpha=alpha, r_star=r_star, ubarf=ubarf,
            f_star0_factor=f_star0_factor,
            parallel=parallel, legacy_nucleation_cs_max=legacy_nucleation_cs_max, model=model,
            settings=ssm_settings
        )
    spectrum_class = ENGINE_SPECTRUM_CLASSES[engine]
    return (spectrum_class.cached if cache else spectrum_class)(
        beta_tilde=beta_tilde, T_star=T_star, g_star=g_star,
        v_wall=v_wall, adiabatic_index=adiabatic_index,
        alpha=alpha, r_star=r_star, ubarf=ubarf,
        f_star0_factor=f_star0_factor,
        legacy_nucleation_cs_max=legacy_nucleation_cs_max
    )


def ssm_model(
        css2: float | None = None,
        csb2: float | None = None,
        model: Model = BAG,
        cache: bool = False) -> Model:
    r"""Equation of state model for the Sound Shell Model (SSM).

    If $c_{s,s}^2$ or $c_{s,b}^2$ differs from the bag model value $1/3$,
    but the model has not been specified, a :py:class:`pttools.models.ConstCSModel` is created.
    Sound speeds that are not given default to the bag model value.

    :param css2: $c_{s,s}^2$, sound speed squared in the symmetric phase
    :param csb2: $c_{s,b}^2$, sound speed squared in the broken phase
    :param model: Equation of state model, which is returned as is if it's not the default bag model
    :param cache: Get the constant sound speed model from the cache
        with :py:meth:`pttools.utils.cache.Cacheable.cached`, creating it if necessary
    :return: Equation of state model
    :raises ValueError: If the constant sound speed model cannot be created with the given sound speeds
    """
    css2 = CS0_2 if css2 is None else css2
    csb2 = CS0_2 if csb2 is None else csb2
    if model is BAG and (not np.isclose(css2, CS0_2) or not np.isclose(csb2, CS0_2)):
        return (ConstCSModel.cached if cache else ConstCSModel)(css2=css2, csb2=csb2)
    return model
