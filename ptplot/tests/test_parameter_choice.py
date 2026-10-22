"""Tests for the parameter choices."""

from django.test import TestCase
import pytest

from ptplot.models import Model, ParameterChoice
from ptplot.science.spectrum import Engine, power_spectrum
from ptplot.tests.plot.test_ps import labels

#: Engines that are quick enough to be drawn in the tests. The SSM is excluded, as it's slow.
ENGINES: tuple[Engine, ...] = (Engine.CosWG20bpl, Engine.CosWG24bpl, Engine.GH21dbpl, Engine.CosWG24dbpl)


def point() -> ParameterChoice:
    """Create a parameter choice that is not saved in the database."""
    return ParameterChoice(
        model=Model(name="Test model", slug="test_model", T_star=100, g_star=100, v_wall=0.9),
        number=1,
        long_label="Test point",
        alpha=0.1,
        beta_tilde=100
    )


class PowerSpectrumFigureTest(TestCase):
    """Tests for :func:`ptplot.models.parameter_choice.ParameterChoice.power_spectrum_figure`."""

    @staticmethod
    def test_single_engine() -> None:
        """A single engine should result in a single curve."""
        fig = point().power_spectrum_figure(engine=Engine.CosWG20bpl)
        assert labels(fig) == [rf"$\Omega_\mathrm{{sw}}$ ({Engine.CosWG20bpl.spectrum.SHORT_NAME})"]

    @staticmethod
    def test_engine_as_str() -> None:
        """The engine should also be accepted as a string, as that's what the forms provide."""
        fig = point().power_spectrum_figure(engine="CosWG20bpl")
        assert labels(fig) == [rf"$\Omega_\mathrm{{sw}}$ ({Engine.CosWG20bpl.spectrum.SHORT_NAME})"]

    @staticmethod
    def test_default_engines() -> None:
        """All engines except those for strong transitions only should be drawn by default."""
        fig = point().power_spectrum_figure()
        assert labels(fig) == [
            rf"$\Omega_\mathrm{{sw}}$ ({engine.spectrum.SHORT_NAME})" for engine in Engine.engines(strong=False)
        ]
        assert rf"$\Omega_\mathrm{{sw}}$ ({Engine.CosWG24bpl.spectrum.SHORT_NAME})" not in labels(fig)

    @staticmethod
    def test_strong_engine_given() -> None:
        """An engine for strong transitions only should be drawn when it's given explicitly, e.g. by the forms."""
        fig = point().power_spectrum_figure(engine="CosWG24bpl")
        assert labels(fig) == [rf"$\Omega_\mathrm{{sw}}$ ({Engine.CosWG24bpl.spectrum.SHORT_NAME})"]

    @staticmethod
    def test_strong_false() -> None:
        """strong=False should exclude the engines for strong transitions only also when they are given."""
        fig = point().power_spectrum_figure(engine=ENGINES, strong=False)
        assert labels(fig) == [
            rf"$\Omega_\mathrm{{sw}}$ ({engine.spectrum.SHORT_NAME})" for engine in ENGINES
            if engine != Engine.CosWG24bpl
        ]

    @staticmethod
    def test_multiple_engines() -> None:
        """Each engine should result in a curve of its own in the same figure."""
        fig = point().power_spectrum_figure(engine=ENGINES)
        assert labels(fig) == [
            rf"$\Omega_\mathrm{{sw}}$ ({engine.spectrum.SHORT_NAME})" for engine in ENGINES
        ]


class PowerSpectrumTest(TestCase):
    """Tests for :func:`ptplot.models.parameter_choice.ParameterChoice.power_spectrum`."""

    @staticmethod
    def test_parameters() -> None:
        """The spectrum should have the parameters of the point, or those of the model if not set for the point."""
        spectrum = point().power_spectrum(engine=Engine.GH21dbpl)
        assert isinstance(spectrum, Engine.GH21dbpl.spectrum)
        assert (spectrum.alpha, spectrum.beta_tilde, spectrum.v_wall, spectrum.T_star, spectrum.g_star) == \
            pytest.approx((0.1, 100, 0.9, 100, 100))

    @staticmethod
    def test_overrides() -> None:
        r"""The parameters can be overridden, e.g. $\beta/H_*$ with $r_*$."""
        p = point()
        r_star = p.power_spectrum().r_star
        spectrum = p.power_spectrum(v_wall=0.5, beta_tilde=None, r_star=r_star)
        reference = power_spectrum(v_wall=0.5, alpha=0.1, r_star=r_star, T_star=100, g_star=100)
        assert (spectrum.v_wall, spectrum.r_star, spectrum.alpha) == pytest.approx((0.5, r_star, 0.1))
        assert spectrum.beta_tilde == pytest.approx(reference.beta_tilde)
        # The r_* of the point is given, so beta/H_* differs from that of the point for another v_wall.
        assert spectrum.beta_tilde != pytest.approx(100)
