"""Tests for the comparisons of lattice simulations to the engines."""

import functools
import logging
from types import SimpleNamespace
import typing as tp

from django.test import TestCase
from matplotlib.figure import Figure
from pttools.lattice import LatticeRun, load_chrw25_runs
import pytest

from ptplot.models import Model, ParameterChoice
from ptplot.science.plot.lattice import YLIM, lattice_curves, lattice_figure, lattice_figures
from ptplot.science.spectrum import CHRW25_NAME, Engine, PowerSpectrumLattice
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
            assert fig_labels[1] == \
                rf"$\Omega_\mathrm{{sw}}$ ({CHRW25_NAME}, $\mathcal{{P}}_\mathrm{{gw}}$, $t \to \infty$)"
            assert fig_labels[2:] == [rf"$\Omega_\mathrm{{sw}}$ ({engine.spectrum.SHORT_NAME})" for engine in ENGINES]

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
    assert [curve.label for curve in curves] == [
        rf"$\Omega_\mathrm{{sw}}$ (sim, $\mathcal{{P}}_\mathrm{{gw}}$, ${spectrum.t_label}$)",
        r"$\Omega_\mathrm{sw}$ (sim, $\mathcal{P}_\mathrm{gw}$, $t \to \infty$)",
        r"$\Omega_\mathrm{sw}$ (sim, $\dot{\mathcal{P}}_\mathrm{gw}$)",
    ]
    assert [curve.f.size for curve in curves] == [1044, 1044, 655]
    assert [len(lattice_curves(spectrum, accumulated=a, asymptote=b)) for a, b in ((True, False), (False, True))] \
        == [1, 1]
