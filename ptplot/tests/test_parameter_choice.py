"""Tests for the parameter choices."""

from django.test import TestCase

from ptplot.models import Model, ParameterChoice
from ptplot.science.spectrum import Engine
from ptplot.tests.plot.test_ps import labels

#: Engines that are quick enough to be drawn in the tests. The SSM is excluded, as it's slow.
ENGINES: tuple[Engine, ...] = (Engine.BPL, Engine.DBPL)


def point() -> ParameterChoice:
    """Create a parameter choice that is not saved in the database."""
    return ParameterChoice(
        model=Model(name="Test model", slug="test_model", T_star=100, g_star=100, v_wall=0.9),
        number=1,
        alpha=0.1,
        beta_tilde=100
    )


class PowerSpectrumFigureTest(TestCase):
    """Tests for :func:`ptplot.models.parameter_choice.ParameterChoice.power_spectrum_figure`."""

    @staticmethod
    def test_single_engine():
        """A single engine should result in a single curve."""
        fig = point().power_spectrum_figure(engine=Engine.BPL)
        assert labels(fig) == [rf"$\Omega_\mathrm{{sw}}$ ({Engine.BPL.spectrum.SHORT_NAME})"]

    @staticmethod
    def test_engine_as_str():
        """The engine should also be accepted as a string, as that's what the forms provide."""
        fig = point().power_spectrum_figure(engine="bpl")
        assert labels(fig) == [rf"$\Omega_\mathrm{{sw}}$ ({Engine.BPL.spectrum.SHORT_NAME})"]

    @staticmethod
    def test_default_engines():
        """All engines should be drawn by default."""
        fig = point().power_spectrum_figure()
        assert labels(fig) == [
            rf"$\Omega_\mathrm{{sw}}$ ({engine.spectrum.SHORT_NAME})" for engine in Engine.engines()
        ]

    @staticmethod
    def test_multiple_engines():
        """Each engine should result in a curve of its own in the same figure."""
        fig = point().power_spectrum_figure(engine=ENGINES)
        assert labels(fig) == [
            rf"$\Omega_\mathrm{{sw}}$ ({engine.spectrum.SHORT_NAME})" for engine in ENGINES
        ]
