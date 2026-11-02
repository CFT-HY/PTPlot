r"""Comparisons of the GW power spectra of lattice simulations to those of the engines.

The lattice simulations are those of :py:mod:`pttools.lattice`, e.g. the runs of :correia_2025:`\ `,
see :py:func:`pttools.lattice.chrw25.load_chrw25_runs`.
The comparisons are created with :py:func:`lattice_comparison`, which is used by both the examples
``examples.ps.plot_lattice`` and ``examples.snr.singlets``, so that their figures have the same style:

- The simulated spectra are drawn with dotted lines, the SSM spectra with dashed lines,
  and the spectra of the other engines with solid lines.
- The simulated spectrum is drawn both from the GW power that has accumulated by the time step (instantaneous),
  and scaled to the asymptotic GW power (extrapolated), see :py:func:`lattice_curves`.
  The instantaneous spectrum is drawn with a faded color.
- The SSM spectrum is drawn both with exponential and simultaneous nucleation, see :py:func:`ssm_curves`.
  The bubbles of the simulations are nucleated simultaneously,
  see :py:attr:`pttools.lattice.run_base.LatticeRunBase.nuc_type`,
  whereas the SSM engine assumes exponential nucleation,
  which is therefore drawn with a faded color.
"""

from collections.abc import Iterable
import csv
from dataclasses import dataclass, replace
import logging
import os
from pathlib import Path
import typing as tp

from matplotlib import rc_context
from matplotlib.figure import Figure
from pttools.lattice import LatticeRun
from pttools.math import as_latex
from pttools.ssm.nucleation import NucType

from ptplot.science import const
from ptplot.science.noise import Noise, resolve_noise
from ptplot.science.plot.lock import matplotlib_lock
from ptplot.science.plot.ps import SpectrumCurve, power_spectrum_figure
from ptplot.science.plot.utils import faded
from ptplot.science.spectrum.base import PowerSpectrum
from ptplot.science.spectrum.engine import Engine
from ptplot.science.spectrum.lattice import CHRW25_NAME, LatticeConversion, PowerSpectrumLattice
from ptplot.science.spectrum.ssm import PowerSpectrumSSM, SSMSettings
from ptplot.science.utils import log_exceptions

if tp.TYPE_CHECKING:
    from ptplot.models import Model, ParameterChoice

logger: logging.Logger = logging.getLogger(__name__)

#: Color of the simulated spectra
COLOR: str = PowerSpectrumLattice.COLOR
#: Color of the simulated spectra from the accumulated GW power at the time step
ACCUMULATED_COLOR: str = faded(COLOR)
#: Color of the simulated spectra converted from the GW power growth rate
RATE_COLOR: str = "brown"
#: Line style of the simulated spectra
LINESTYLE: str = ":"
#: Abbreviations of the nucleation types in the labels
NUC_TYPE_LABELS: dict[NucType, str] = {NucType.EXPONENTIAL: "exp.", NucType.SIMULTANEOUS: "simult."}
#: Nucleation types of the SSM spectra
SSM_NUC_TYPES: tuple[NucType, ...] = (NucType.EXPONENTIAL, NucType.SIMULTANEOUS)
#: Limits of the y-axis of the figures.
#: The legend has many entries, and is therefore placed above the spectra.
YLIM: tuple[float, float] = (1e-16, 1e-6)


@dataclass(frozen=True, slots=True)
class LatticeComparison:
    """Spectra of a lattice simulation and of the engines, with their SNRs, for drawing them in figures.

    The spectra are computed only once, so that multiple versions of the figure can be drawn,
    e.g. with and without the title, see :py:meth:`figure`.
    """

    #: Curves by their names, which have their SNRs computed
    curves: dict[str, SpectrumCurve]
    #: Noise curve against which the SNRs have been computed
    noise: Noise
    #: Default title of the figure
    title: str | None = None

    @matplotlib_lock
    def figure(self, title: bool | str = True, snr: bool = True) -> Figure:
        """Draw the spectra in a power spectrum figure, see :py:func:`ptplot.science.plot.ps.power_spectrum_figure`.

        :param title: Title of the figure, True for the default title :py:attr:`title`, or False for no title
        :param snr: Whether to print the SNR values in the legend
        :return: Power spectrum figure
        """
        fig = power_spectrum_figure(
            [],
            noise=self.noise,
            curves=self.curves.values(),
            ylim=YLIM,
            snr=snr,
            title=self.title if title is True else (title or None)
        )
        with rc_context(const.DEFAULT_RC_CONTEXT):
            # The legend has many entries, so a smaller font is used.
            fig.axes[0].legend(loc="upper right", fontsize="small")
        return fig

    def save_csv(self, path: str | os.PathLike[str]) -> Path:
        """Save the SNRs of the curves as a CSV file with the columns ``name``, ``label`` and ``snr``.

        :param path: Path of the file, whose parent directories are created if needed
        :return: Path of the saved file
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(("name", "label", "snr"))
            for name, curve in self.curves.items():
                writer.writerow((name, curve.label, curve.snr))
        return path

    @property
    def snrs(self) -> dict[str, float]:
        """SNRs of the curves by their names."""
        return {name: tp.cast(float, curve.snr) for name, curve in self.curves.items()}


def lattice_comparison(
        lattice: PowerSpectrumLattice,
        spectra: Iterable[PowerSpectrum],
        noise: Noise | None = None,
        title: str | None = None,
        accumulated: bool = True,
        asymptote: bool = True,
        rate: bool = False,
        nuc_types: Iterable[NucType] = SSM_NUC_TYPES) -> LatticeComparison:
    r"""Compare the GW power spectra of a lattice simulation to those of the engines.

    The curves are the simulated spectra of :py:func:`lattice_curves`, followed by the spectra of the engines.
    The SSM spectra are drawn with each of the nucleation types, see :py:func:`ssm_curves`.
    The SNRs of all the curves are computed against the noise curve.

    :param lattice: spectrum of the simulation
    :param spectra: spectra of the engines
    :param noise: noise curve, defaults to the default noise curve
    :param title: default title of the figure
    :param accumulated: whether to draw the simulated spectrum from the accumulated GW power at the time step
    :param asymptote: whether to draw the simulated spectrum scaled to the asymptotic GW power
    :param rate: whether to draw the simulated spectrum converted from the GW power growth rate
    :param nuc_types: nucleation types of the SSM spectra
    :return: the comparison
    """
    noise = resolve_noise(noise)
    nuc_types = tuple(nuc_types)
    curves = {
        name: replace(curve, snr=PowerSpectrum.snr(curve.f, curve.omgw0_h2, noise))
        for name, curve in lattice_curves(lattice, accumulated=accumulated, asymptote=asymptote, rate=rate).items()
    }
    for spectrum in spectra:
        if isinstance(spectrum, PowerSpectrumSSM):
            curves |= ssm_curves(spectrum, noise, nuc_types=nuc_types)
            continue
        omgw0_h2, snr = spectrum.power_spectrum(noise.f, noise=noise)
        curves[spectrum.SHORT_NAME] = SpectrumCurve(
            f=noise.f, omgw0_h2=omgw0_h2, label=spectrum.SHORT_NAME,
            color=spectrum.COLOR, linestyle=spectrum.LINESTYLE, snr=snr
        )
    return LatticeComparison(curves=curves, noise=noise, title=title)


def lattice_comparison_at_point(
        point: "ParameterChoice",
        run: LatticeRun,
        engines: Iterable[Engine] | None = None,
        name: str = CHRW25_NAME,
        noise: Noise | None = None,
        ssm_settings: SSMSettings | None = None) -> LatticeComparison:
    r"""Compare the GW power spectra of a lattice simulation to those of the engines at a point.

    All the spectra have the $v_\text{wall}$ of the simulation, and the engines are given the $\beta/H_*$ of the point,
    from which they compute $r_*$ with this $v_\text{wall}$.
    The other parameters are those of the point.
    The simulations are scale-free, and the lattice spectra are therefore evaluated at the $r_*$ of the SSM spectrum.
    For deflagrations and hybrids, this includes the bubble spacing enlargement factor $\Lambda(h_x)$
    due to the thermal suppression of nucleation, :ajmi_2022:`\ ` eq. 77,

    $$r_* = \Lambda(h_x) r_*(0), \quad r_*(0) = (8\pi)^\frac{1}{3} \frac{{v}_\text{wall}}{\tilde{\beta}},$$

    where $\tilde{\beta} \equiv \beta/H_*$, see :py:func:`pttools.ssm.nucleation.R_star`.
    The other engines use $r_*(0)$, and their spectra are therefore not evaluated at the same $r_*$
    as the lattice spectra for deflagrations and hybrids.
    For detonations, $\Lambda = 1$, and all the spectra have the same $r_*$.
    See :py:func:`lattice_comparison`.

    :param point: Point whose parameters are used
    :param run: Lattice simulation
    :param engines: Engines whose spectra are drawn, which must include the SSM,
        defaults to all the engines except those for strong transitions only, i.e. ``CosWG24bpl``
    :param name: Name of the simulation in the labels
    :param noise: Noise curve, defaults to the default noise curve
    :param ssm_settings: Accuracy settings of the PTtools spectra of the SSM engine
    :return: The comparison, whose default title contains the parameters of the point and the simulation
    :raises ValueError: If the engines do not include the SSM
    """
    engines = Engine.engines(engines, strong=engines is not None)
    if Engine.SSM not in engines:
        raise ValueError(
            f"The engines must include the SSM, whose r_star is used for the lattice spectra. Got: {engines}"
        )
    spectra = [
        point.power_spectrum(engine=engine, v_wall=run.v_wall, ssm_settings=ssm_settings)
        for engine in engines
    ]
    r_star = next(spectrum for spectrum in spectra if isinstance(spectrum, PowerSpectrumSSM)).r_star
    lattice = PowerSpectrumLattice(run, r_star=r_star, T_star=point.T_star_value, g_star=point.g_star_value, name=name)
    return lattice_comparison(
        lattice, spectra, noise=noise,
        title=f"{point.model.name}, point {point.number}\n{point.figure_title(v_wall=False)}\n"
              rf"{run.label_latex}, $r_* = {as_latex(r_star)}$"
    )


def lattice_comparisons(
        model: "Model",
        runs: dict[str, LatticeRun],
        engines: Iterable[Engine] | None = None,
        name: str = CHRW25_NAME,
        ssm_settings: SSMSettings | None = None) -> dict[str, LatticeComparison]:
    r"""Compare the GW power spectra of lattice simulations to those of the engines at the points of a model.

    For each simulation, the point of the model whose $\alpha$ is closest to the $\alpha_n$ of the simulation
    is used, see :py:meth:`ptplot.models.model.Model.closest_point` and :py:func:`lattice_comparison_at_point`.
    If a comparison cannot be created, the error is logged, and the other comparisons are created.

    :param model: Model whose points are used
    :param runs: Lattice simulations by name, e.g. from :py:func:`pttools.lattice.chrw25.load_chrw25_runs`
    :param engines: Engines whose spectra are drawn, which must include the SSM,
        defaults to all the engines except those for strong transitions only, i.e. ``CosWG24bpl``
    :param name: Name of the simulations in the labels
    :param ssm_settings: Accuracy settings of the PTtools spectra of the SSM engine
    :return: Comparisons by the names of the simulations
    """
    engines = None if engines is None else list(engines)
    comparisons: dict[str, LatticeComparison] = {}
    for run_name, run in runs.items():
        with log_exceptions(logger, "Failed to plot the lattice spectra of %s for %s", run_name, model.name):
            comparisons[run_name] = lattice_comparison_at_point(
                model.closest_point(run.alpha_n), run, engines, name=name, ssm_settings=ssm_settings
            )
    return comparisons


def lattice_curves(
        spectrum: PowerSpectrumLattice,
        accumulated: bool = True,
        asymptote: bool = True,
        rate: bool = False) -> dict[str, SpectrumCurve]:
    r"""Curves of the spectra of a lattice simulation for :py:func:`ptplot.science.plot.ps.power_spectrum_figure`.

    The curves are drawn only below the lattice artifact at high $k$,
    see :py:attr:`ptplot.science.spectrum.lattice.PowerSpectrumLattice.valid`,
    and therefore their SNRs are also computed only there.

    :param spectrum: spectrum of the simulation
    :param accumulated: whether to draw the spectrum from the accumulated GW power at the time step,
        see :py:attr:`ptplot.science.spectrum.lattice.PowerSpectrumLattice.omgw0_h2`
    :param asymptote: whether to draw the spectrum scaled to the asymptotic GW power,
        see :py:attr:`ptplot.science.spectrum.lattice.PowerSpectrumLattice.omgw0_h2_asymptote`
    :param rate: whether to draw the spectrum converted from the GW power growth rate,
        see :py:attr:`ptplot.science.spectrum.lattice.PowerSpectrumLattice.omgw0_h2_rate`
    :return: curves by the names ``NAME_CONVERSION``, where ``CONVERSION`` is that of
        :py:class:`ptplot.science.spectrum.lattice.LatticeConversion`
    """
    f = spectrum.f
    valid = spectrum.valid
    name = spectrum.name
    curves: dict[str, SpectrumCurve] = {}
    if accumulated:
        curves[f"{name}_{LatticeConversion.ACCUMULATED}"] = SpectrumCurve(
            f=f[valid], omgw0_h2=spectrum.omgw0_h2[valid], color=ACCUMULATED_COLOR, linestyle=LINESTYLE,
            label=rf"{name}, $\mathcal{{P}}_\mathrm{{gw}}$, ${spectrum.t_label}$"
        )
    if asymptote:
        curves[f"{name}_{LatticeConversion.ASYMPTOTE}"] = SpectrumCurve(
            f=f[valid], omgw0_h2=spectrum.omgw0_h2_asymptote[valid], color=COLOR, linestyle=LINESTYLE,
            label=rf"{name}, $\mathcal{{P}}_\mathrm{{gw}}$, $t \to \infty$"
        )
    if rate:
        valid_rate = spectrum.valid_rate
        curves[f"{name}_{LatticeConversion.RATE}"] = SpectrumCurve(
            f=f[valid_rate], omgw0_h2=spectrum.omgw0_h2_rate[valid_rate], color=RATE_COLOR, linestyle=LINESTYLE,
            label=rf"{name}, $\dot{{\mathcal{{P}}}}_\mathrm{{gw}}$"
        )
    return curves


def lattice_figure(
        point: "ParameterChoice",
        run: LatticeRun,
        engines: Iterable[Engine] | None = None,
        name: str = CHRW25_NAME,
        title: bool | str = True,
        snr: bool = True,
        ssm_settings: SSMSettings | None = None) -> Figure:
    r"""Compare the GW power spectra of a lattice simulation to those of the engines at a point.

    See :py:func:`lattice_comparison_at_point`.

    :param point: Point whose parameters are used
    :param run: Lattice simulation
    :param engines: Engines whose spectra are drawn, which must include the SSM,
        defaults to all the engines except those for strong transitions only, i.e. ``CosWG24bpl``
    :param name: Name of the simulation in the labels
    :param title: Title of the figure, True for the default title with the parameters, or False for no title
    :param snr: Whether to print the SNR values in the legend
    :param ssm_settings: Accuracy settings of the PTtools spectra of the SSM engine
    :return: Power spectrum figure
    """
    return lattice_comparison_at_point(
        point, run, engines, name=name, ssm_settings=ssm_settings
    ).figure(title=title, snr=snr)


def lattice_figures(
        model: "Model",
        runs: dict[str, LatticeRun],
        engines: Iterable[Engine] | None = None,
        name: str = CHRW25_NAME,
        title: bool | str = True,
        snr: bool = True,
        ssm_settings: SSMSettings | None = None) -> dict[str, Figure]:
    r"""Compare the GW power spectra of lattice simulations to those of the engines at the points of a model.

    See :py:func:`lattice_comparisons`.

    :param model: Model whose points are used
    :param runs: Lattice simulations by name, e.g. from :py:func:`pttools.lattice.chrw25.load_chrw25_runs`
    :param engines: Engines whose spectra are drawn, which must include the SSM,
        defaults to all the engines except those for strong transitions only, i.e. ``CosWG24bpl``
    :param name: Name of the simulations in the labels
    :param title: Title of the figures, True for the default titles with the parameters, or False for no titles
    :param snr: Whether to print the SNR values in the legends
    :param ssm_settings: Accuracy settings of the PTtools spectra of the SSM engine
    :return: Figures by the names of the simulations
    """
    return {
        run_name: comparison.figure(title=title, snr=snr)
        for run_name, comparison in lattice_comparisons(
            model, runs, engines, name=name, ssm_settings=ssm_settings
        ).items()
    }


def ssm_curves(
        ssm: PowerSpectrumSSM,
        noise: Noise | None = None,
        nuc_types: Iterable[NucType] = SSM_NUC_TYPES) -> dict[str, SpectrumCurve]:
    r"""Curves of the SSM spectrum with different nucleation types, with their SNRs.

    The spectra are those of :py:meth:`ptplot.science.spectrum.ssm.PowerSpectrumSSM.power_spectrum`
    with each nucleation type, and therefore have the same $r_*$.
    The exponential nucleation is that of the SSM engine,
    and it's drawn with a faded color to distinguish it from the simultaneous nucleation of the simulations.
    After this, :py:attr:`ptplot.science.spectrum.ssm.PowerSpectrumSSM.spectrum` is the spectrum
    of the last nucleation type.

    :param ssm: SSM spectrum
    :param noise: noise curve, defaults to the default noise curve
    :param nuc_types: nucleation types
    :return: curves by the names ``SSM_NUCTYPE``
    """
    noise = resolve_noise(noise)
    curves: dict[str, SpectrumCurve] = {}
    for nuc_type in nuc_types:
        omgw0_h2, snr = ssm.power_spectrum(noise.f, noise=noise, nuc_type=nuc_type)
        color = faded(ssm.COLOR) if nuc_type == NucType.EXPONENTIAL else ssm.COLOR
        curves[f"{ssm.SHORT_NAME}_{nuc_type}"] = SpectrumCurve(
            f=noise.f, omgw0_h2=omgw0_h2, label=f"{ssm.SHORT_NAME}, {NUC_TYPE_LABELS[nuc_type]}",
            color=color, linestyle=ssm.LINESTYLE, snr=snr
        )
    return curves
