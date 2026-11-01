"""Tests for the comparisons of lattice simulations to the engines."""

import csv
import functools
import logging
from pathlib import Path
from types import SimpleNamespace
import typing as tp

from django.test import TestCase
from matplotlib.figure import Figure
import numpy as np
from pttools.lattice import LatticeRun, load_chrw25_runs
from pttools.math import as_latex
from pttools.ssm.nucleation import NucType
import pytest

from ptplot.models import Model, ParameterChoice
from ptplot.science.noise import resolve_noise
from ptplot.science.plot.lattice import (
    ACCUMULATED_COLOR,
    COLOR,
    LINESTYLE,
    YLIM,
    lattice_comparison,
    lattice_curves,
    lattice_figure,
    lattice_figures,
    ssm_curves,
)
from ptplot.science.plot.utils import faded
from ptplot.science.spectrum import CHRW25_NAME, Engine, PowerSpectrumLattice, PowerSpectrumSSM, SSMSettings
from ptplot.tests.plot.test_ps import labels

#: Engines that are quick enough to be drawn in the tests. The SSM is excluded, as it's slow.
ENGINES: tuple[Engine, ...] = (Engine.CosWG20bpl, Engine.GH21dbpl)


@functools.cache
def runs() -> dict[str, LatticeRun]:
    """The lattice simulations of Correia et al., or an empty dict if the data is not available."""
    return load_chrw25_runs(missing_ok=True)


class LatticeFigureTest(TestCase):
    """Tests for :py:mod:`ptplot.science.plot.lattice`."""

    model: Model

    @classmethod
    def setUpTestData(cls) -> None:
        """Create a model with points of different strengths."""
        cls.model = Model.objects.create(
            name="Test model", slug="test_model", v_wall=0.95, T_star=100, g_star=100, has_scenarios=False
        )
        for number, alpha in enumerate((0.1, 0.45, 0.7), start=1):
            ParameterChoice.objects.create(model=cls.model, number=number, alpha=alpha, beta_tilde=100)

    def test_lattice_figures(self) -> None:
        """Each simulation should be compared at the point whose alpha is closest to that of the simulation."""
        if not runs():
            pytest.skip("The data of the lattice simulations is not available.")
        figs = lattice_figures(self.model, runs(), engines=ENGINES)
        assert list(figs) == list(runs())
        for name, fig in figs.items():
            run = runs()[name]
            point = self.model.closest_point(run.alpha_n)
            ax = fig.get_axes()[0]
            assert ax.get_ylim() == pytest.approx(YLIM)
            assert point.figure_title(v_wall=False) in ax.get_title()
            assert point.figure_title() not in ax.get_title()
            fig_labels = labels(fig)
            assert fig_labels[0].startswith(rf"{CHRW25_NAME}, $\mathcal{{P}}_\mathrm{{gw}}$, $t=")
            assert fig_labels[1] == rf"{CHRW25_NAME}, $\mathcal{{P}}_\mathrm{{gw}}$, $t \to \infty$"
            assert fig_labels[2:] == [engine.spectrum.SHORT_NAME for engine in ENGINES]
            lines = ax.get_lines()
            assert [(line.get_color(), line.get_linestyle()) for line in lines[:2]] == \
                [(ACCUMULATED_COLOR, LINESTYLE), (COLOR, LINESTYLE)]
            assert [line.get_linestyle() for line in lines[2:]] == ["-"] * len(ENGINES)

    def test_lattice_figures_paper(self) -> None:
        """The title and the SNRs can be left out, and the title can be overridden."""
        if not runs():
            pytest.skip("The data of the lattice simulations is not available.")
        for fig in lattice_figures(self.model, runs(), engines=ENGINES, title=False, snr=False).values():
            assert fig.get_axes()[0].get_title() == ""
            assert all("SNR" not in label for label in labels(fig, strip_snr=False))
        run = runs()["detonation"]
        fig = lattice_figure(self.model.closest_point(run.alpha_n), run, engines=ENGINES, title="Test title")
        assert fig.get_axes()[0].get_title() == "Test title"
        assert all("SNR=" in label for label in labels(fig, strip_snr=False))

    @staticmethod
    def test_lattice_figure_v_wall() -> None:
        """The spectra of the engines should have the v_wall of the simulation and the r_* of the point."""
        if not runs():
            pytest.skip("The data of the lattice simulations is not available.")
        run = next(iter(runs().values()))
        point = ParameterChoice(
            model=Model(name="Test", slug="test", T_star=100, g_star=100, v_wall=0.95),
            number=1, alpha=0.5, beta_tilde=100
        )
        assert isinstance(lattice_figure(point, run, engines=ENGINES[:1]), Figure)
        r_star = point.power_spectrum(v_wall=run.v_wall).r_star
        assert r_star != pytest.approx(point.power_spectrum().r_star)

    def test_lattice_figures_error(self) -> None:
        """A figure that cannot be created should be logged and skipped."""
        empty = Model.objects.create(
            name="Empty model", slug="empty_model", v_wall=0.95, T_star=100, g_star=100, has_scenarios=False
        )
        # The run is not used, as the model has no points to compare it with.
        run = tp.cast(LatticeRun, SimpleNamespace(alpha_n=0.5))
        with self.assertLogs("ptplot.science.plot.lattice", level=logging.ERROR) as logs:
            figs = lattice_figures(empty, {"run": run}, engines=ENGINES)
        assert figs == {}
        assert "Failed to plot the lattice spectra of run for Empty model" in logs.output[0]


def test_lattice_curves() -> None:
    """The curves should be truncated at the lattice artifact, and drawn only when requested."""
    if not runs():
        pytest.skip("The data of the lattice simulations is not available.")
    run = runs()["detonation"]
    spectrum = PowerSpectrumLattice(run, 18000, 12000, r_star=0.1, name="sim")
    curves = lattice_curves(spectrum, accumulated=True, asymptote=True, rate=True)
    assert list(curves) == ["sim_accumulated", "sim_asymptote", "sim_rate"]
    assert [curve.label for curve in curves.values()] == [
        rf"sim, $\mathcal{{P}}_\mathrm{{gw}}$, ${spectrum.t_label}$",
        r"sim, $\mathcal{P}_\mathrm{gw}$, $t \to \infty$",
        r"sim, $\dot{\mathcal{P}}_\mathrm{gw}$",
    ]
    assert [curve.f.size for curve in curves.values()] == [1044, 1044, 655]
    assert {curve.linestyle for curve in curves.values()} == {LINESTYLE}
    assert [len(lattice_curves(spectrum, accumulated=a, asymptote=b)) for a, b in ((True, False), (False, True))] \
        == [1, 1]


def test_lattice_comparison(tmp_path: Path) -> None:
    """The SNRs should be computed once, printed in the legend, and saved as CSV."""
    if not runs():
        pytest.skip("The data of the lattice simulations is not available.")
    run = runs()["detonation"]
    lattice = PowerSpectrumLattice(run, r_star=0.1, name="sim")
    spectra = [engine.spectrum(v_wall=run.v_wall, alpha=run.alpha_n, r_star=0.1) for engine in ENGINES]
    comparison = lattice_comparison(lattice, spectra, title="Title")
    names = ["sim_accumulated", "sim_asymptote"] + [engine.spectrum.SHORT_NAME for engine in ENGINES]
    assert list(comparison.snrs) == names
    noise = resolve_noise(None)
    for spectrum in spectra:
        assert comparison.snrs[spectrum.SHORT_NAME] == pytest.approx(spectrum.power_spectrum(noise.f, noise)[1])
    assert comparison.figure().get_axes()[0].get_title() == "Title"
    fig_labels = labels(comparison.figure(), strip_snr=False)
    assert fig_labels == [
        f"{curve.label}, SNR={as_latex(curve.snr, math_mode=True)}" for curve in comparison.curves.values()
    ]

    path = comparison.save_csv(tmp_path / "sub" / "snr.csv")
    with path.open(encoding="utf-8") as file:
        rows = list(csv.DictReader(file))
    assert [row["name"] for row in rows] == names
    assert [float(row["snr"]) for row in rows] == pytest.approx(list(comparison.snrs.values()))


def test_ssm_curves() -> None:
    """The exponential nucleation should be that of the SSM engine, and faded."""
    noise = resolve_noise(None)
    settings = SSMSettings(n_z_lookup=500, n_t=100)
    ssm = PowerSpectrumSSM(v_wall=0.92, alpha=0.67, r_star=0.1, settings=settings)
    curves = ssm_curves(ssm, noise)
    assert list(curves) == ["SSM_exponential", "SSM_simultaneous"]
    exp, sim = curves.values()
    assert (exp.label, sim.label) == ("SSM, exp.", "SSM, simult.")
    assert (exp.color, sim.color) == (faded(PowerSpectrumSSM.COLOR), PowerSpectrumSSM.COLOR)
    assert exp.linestyle == sim.linestyle == PowerSpectrumSSM.LINESTYLE
    omgw0_h2, snr = ssm.power_spectrum(noise.f, noise)
    np.testing.assert_allclose(exp.omgw0_h2, omgw0_h2)
    assert exp.snr == pytest.approx(snr)
    # Simultaneous nucleation gives a narrower distribution of bubble sizes, and therefore a peak at higher f.
    assert noise.f[np.argmax(sim.omgw0_h2)] > noise.f[np.argmax(exp.omgw0_h2)]
    assert list(ssm_curves(ssm, noise, nuc_types=(NucType.SIMULTANEOUS,))) == ["SSM_simultaneous"]
