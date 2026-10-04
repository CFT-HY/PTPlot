r"""Exportable fields of the power spectra.

The spectra can be exported with :py:class:`pttools.export.exporter.Exporter`,
which stores the spectra of each engine in a table of its own,
see :py:attr:`ptplot.science.spectrum.base.PowerSpectrum.TABLE`.
The frequencies $f$ of the last computed spectrum are a :py:attr:`~pttools.utils.fields.FieldShape.GRID` field,
and therefore all the spectra of an engine in a file must have been computed at the same frequencies.

The fields have no :py:attr:`~pttools.utils.fields.Preset.INIT` preset,
as recreating the spectra from an exported file is not supported.
They are computed in milliseconds, and can therefore be recreated from the parameters if needed.

The spectra of the Sound Shell Model are computed with PTtools,
and they are therefore exported as :py:class:`pttools.omgw0.spectrum.Spectrum` objects instead,
see :py:meth:`ptplot.science.spectrum.ssm.PowerSpectrumSSM.record`.
"""

from pttools.utils.fields import (
    PRESETS_FULL,
    PRESETS_MINIMAL_FULL,
    Field,
    Fields,
    FieldShape,
)

__all__ = [
    "ANALYTIC_SPECTRUM_FIELDS",
    "F_AXIS",
    "POWER_SPECTRUM_FIELDS",
]

#: Name of the axis of the spectra, i.e. the frequencies $f$
F_AXIS: str = "f"

#: Fields of :py:class:`ptplot.science.spectrum.base.PowerSpectrum`
POWER_SPECTRUM_FIELDS: Fields = Fields(
    # Parameters
    Field("v_wall", presets=PRESETS_MINIMAL_FULL, description=r"$v_\text{wall}$, wall speed"),
    Field("alpha", presets=PRESETS_MINIMAL_FULL, description=r"$\alpha$, phase transition strength"),
    Field(
        "beta_tilde", presets=PRESETS_MINIMAL_FULL,
        description=r"$\tilde{\beta} = \beta / H_*$, inverse phase transition duration relative to $H_*$"),
    Field("r_star", presets=PRESETS_MINIMAL_FULL, description="$r_*$, Hubble-scaled mean bubble spacing"),
    Field("ubarf", presets=PRESETS_MINIMAL_FULL, description=r"$\bar{U}_f$, RMS fluid velocity"),
    Field("T_star", presets=PRESETS_MINIMAL_FULL, description="$T_*$, transition temperature"),
    Field("g_star", presets=PRESETS_MINIMAL_FULL, description="$g_*$, degrees of freedom"),
    Field("adiabatic_index", presets=PRESETS_MINIMAL_FULL, description=r"$\Gamma$, mean adiabatic index"),
    Field("cs", presets=PRESETS_FULL, description="$c_s$, speed of sound"),
    Field("nu_gdh2024", presets=PRESETS_FULL, description=r"$\nu_\text{gdh2024}$"),
    Field("N_sh", presets=PRESETS_FULL, description=r"$N_\text{sh}$, number of shock formation times"),
    # Computed values
    # The descriptions of the properties and methods are taken from their docstrings.
    Field("H_star_eta_sh", presets=PRESETS_MINIMAL_FULL),
    Field("H_star_eta_v", presets=PRESETS_FULL),
    Field("J", call=True, presets=PRESETS_FULL),
    Field("kinetic_energy_fraction", presets=PRESETS_FULL),
    Field("source_lifetime_factor", call=True, presets=PRESETS_FULL),
    # The results of the last call of power_spectrum()
    Field(
        "f", getter="last_f", shape=FieldShape.GRID, axis=F_AXIS, presets=PRESETS_MINIMAL_FULL,
        description="$f$, frequencies today"),
    Field(
        "omgw0_h2", getter="last_omgw0_h2", shape=FieldShape.ARRAY, axis=F_AXIS, presets=PRESETS_MINIMAL_FULL,
        description=r"$\Omega_{\text{gw},0} h^2$, GW power spectrum today"),
    Field("snr", getter="last_snr", presets=PRESETS_MINIMAL_FULL, description="signal-to-noise ratio"),
)

#: Fields of the analytic power spectra,
#: :py:class:`ptplot.science.spectrum.base2020.PowerSpectrum2020` and
#: :py:class:`ptplot.science.spectrum.base2024.PowerSpectrum2024`
ANALYTIC_SPECTRUM_FIELDS: Fields = Fields(
    POWER_SPECTRUM_FIELDS,
    Field("f_peak", call=True, presets=PRESETS_MINIMAL_FULL),
)
