r"""Comparisons of the GW power spectra of lattice simulations to those of the engines.

The lattice simulations are those of :py:mod:`pttools.lattice`, e.g. the runs of :correia_2025:`\ `,
see :py:func:`pttools.lattice.chrw25.load_chrw25_runs`.
"""

from collections.abc import Iterable
import logging
import typing as tp

from matplotlib.figure import Figure
from pttools.lattice import LatticeRun
from pttools.math import as_latex

from ptplot.science.plot.ps import SpectrumCurve, power_spectrum_figure
from ptplot.science.spectrum.engine import Engine
from ptplot.science.spectrum.lattice import CHRW25_NAME, PowerSpectrumLattice
from ptplot.science.utils import log_exceptions

if tp.TYPE_CHECKING:
    from ptplot.models import Model, ParameterChoice

logger: logging.Logger = logging.getLogger(__name__)

#: Color of the simulated spectra
COLOR: str = "black"
#: Color of the simulated spectra converted from the GW power growth rate
RATE_COLOR: str = "grey"
#: Line style of the simulated spectra from the accumulated GW power at the time step
LINESTYLE: str = ":"
#: Line style of the simulated spectra scaled to the asymptotic GW power
ASYMPTOTE_LINESTYLE: str = "--"
#: Line style of the simulated spectra converted from the GW power growth rate
RATE_LINESTYLE: str = ":"
#: Limits of the y-axis of the figures.
#: The legend has many entries, and is therefore placed above the spectra.
YLIM: tuple[float, float] = (1e-16, 1e-6)


def lattice_curves(
        spectrum: PowerSpectrumLattice,
        accumulated: bool = True,
        asymptote: bool = True,
        rate: bool = False) -> list[SpectrumCurve]:
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
    :return: curves
    """
    f = spectrum.f
    valid = spectrum.valid
    label = rf"$\Omega_\mathrm{{sw}}$ ({spectrum.name}"
    curves = []
    if accumulated:
        curves.append(SpectrumCurve(
            f=f[valid], omgw0_h2=spectrum.omgw0_h2[valid], color=COLOR, linestyle=LINESTYLE,
            label=rf"{label}, $\mathcal{{P}}_\mathrm{{gw}}$, ${spectrum.t_label}$)"
        ))
    if asymptote:
        curves.append(SpectrumCurve(
            f=f[valid], omgw0_h2=spectrum.omgw0_h2_asymptote[valid], color=COLOR, linestyle=ASYMPTOTE_LINESTYLE,
            label=rf"{label}, $\mathcal{{P}}_\mathrm{{gw}}$, $t \to \infty$)"
        ))
    if rate:
        valid_rate = spectrum.valid_rate
        curves.append(SpectrumCurve(
            f=f[valid_rate], omgw0_h2=spectrum.omgw0_h2_rate[valid_rate], color=RATE_COLOR, linestyle=RATE_LINESTYLE,
            label=rf"{label}, $\dot{{\mathcal{{P}}}}_\mathrm{{gw}}$)"
        ))
    return curves


def lattice_figure(
        point: "ParameterChoice",
        run: LatticeRun,
        engines: Iterable[Engine] | None = None,
        name: str = CHRW25_NAME) -> Figure:
    r"""Compare the GW power spectra of a lattice simulation to those of the engines at a point.

    The figure contains the GW power spectrum of the last time step of the simulation
    and the spectrum scaled to its asymptote, see :py:func:`lattice_curves`, and the spectra of the engines.
    All the spectra have the $v_\text{wall}$ of the simulation,
    and the $r_*$ that corresponds to the $\beta/H_*$ of the point with this $v_\text{wall}$.
    The other parameters are those of the point.

    :param point: Point whose parameters are used
    :param run: Lattice simulation
    :param engines: Engines whose spectra are drawn, defaults to all the engines
    :param name: Name of the simulation in the labels
    :return: Power spectrum figure
    """
    r_star = point.power_spectrum(v_wall=run.v_wall).r_star
    spectrum = PowerSpectrumLattice(run, r_star=r_star, T_star=point.T_star_value, g_star=point.g_star_value, name=name)
    spectra = [point.power_spectrum(engine=engine, v_wall=run.v_wall) for engine in Engine.engines(engines)]
    return power_spectrum_figure(
        spectra,
        curves=lattice_curves(spectrum),
        ylim=YLIM,
        title=f"{point.model.name}, point {point.number}\n{point.figure_title(v_wall=False)}\n"
              rf"{run.label_latex}, $r_* = {as_latex(r_star)}$"
    )


def lattice_figures(
        model: "Model",
        runs: dict[str, LatticeRun],
        engines: Iterable[Engine] | None = None,
        name: str = CHRW25_NAME) -> dict[str, Figure]:
    r"""Compare the GW power spectra of lattice simulations to those of the engines at the points of a model.

    For each simulation, the point of the model whose $\alpha$ is closest to the $\alpha_n$ of the simulation
    is used, see :py:meth:`ptplot.models.model.Model.closest_point` and :py:func:`lattice_figure`.
    If a figure cannot be created, the error is logged, and the other figures are created.

    :param model: Model whose points are used
    :param runs: Lattice simulations by name, e.g. from :py:func:`pttools.lattice.chrw25.load_chrw25_runs`
    :param engines: Engines whose spectra are drawn, defaults to all the engines
    :param name: Name of the simulations in the labels
    :return: Figures by the names of the simulations
    """
    engines = None if engines is None else list(engines)
    figs: dict[str, Figure] = {}
    for run_name, run in runs.items():
        with log_exceptions(logger, "Failed to plot the lattice spectra of %s for %s", run_name, model.name):
            figs[run_name] = lattice_figure(model.closest_point(run.alpha_n), run, engines, name=name)
    return figs
