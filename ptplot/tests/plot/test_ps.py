"""Tests for the power spectrum figure."""

from django.test import TestCase
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
import pytest

from ptplot.science import const
from ptplot.science.plot.ps import power_spectrum_figure
from ptplot.science.spectrum import PowerSpectrum, PowerSpectrumBPL, PowerSpectrumDBPL

#: Engines that are quick enough to be drawn in the tests. The SSM is excluded, as it's slow.
SPECTRUM_CLASSES: tuple[type[PowerSpectrum], ...] = (PowerSpectrumBPL, PowerSpectrumDBPL)


def spectra() -> list[PowerSpectrum]:
    """Create one power spectrum of each engine that is tested."""
    return [
        spectrum_class(
            v_wall=const.DEFAULT_V_WALL, alpha=const.DEFAULT_ALPHA, beta_tilde=const.DEFAULT_BETA_TILDE
        )
        for spectrum_class in SPECTRUM_CLASSES
    ]


def labels(fig: Figure) -> list[str]:
    """Get the legend labels of the curves of a figure."""
    return [
        label
        for label in (
            str(line.get_label())
            for line in fig.get_axes()[0].get_children()
            if isinstance(line, Line2D)
        )
        # Matplotlib marks the artists that are excluded from the legend with an underscore.
        if not label.startswith("_")
    ]


class PowerSpectrumFigureTest(TestCase):
    """Tests for :func:`ptplot.science.plot.ps.power_spectrum_figure`."""

    @staticmethod
    def test_single():
        """A single spectrum should be drawn with its engine in the legend."""
        spectrum = spectra()[0]
        fig = power_spectrum_figure(spectrum)
        assert labels(fig) == [rf"$\Omega_\mathrm{{sw}}$ ({spectrum.SHORT_NAME})"]

    @staticmethod
    def test_multiple():
        """Each of the spectra should be drawn with its own color and engine in the legend."""
        spectra_list = spectra()
        fig = power_spectrum_figure(spectra_list)
        ax = fig.get_axes()[0]
        assert labels(fig) == [
            rf"$\Omega_\mathrm{{sw}}$ ({spectrum.SHORT_NAME})" for spectrum in spectra_list
        ]
        assert [line.get_color() for line in ax.get_lines()] == [
            spectrum.COLOR for spectrum in spectra_list
        ]

    @staticmethod
    def test_multiple_with_turbulence():
        """Each component of each spectrum should be drawn with its engine in the legend."""
        spectra_list = spectra()
        fig = power_spectrum_figure(spectra_list, sw_only=False)
        for spectrum in spectra_list:
            assert rf"$\Omega_\mathrm{{sw}}$ ({spectrum.SHORT_NAME})" in labels(fig)
        # Only the BPL has turbulence curves.
        assert rf"$\Omega_\mathrm{{turb}}$ ({PowerSpectrumBPL.SHORT_NAME})" in labels(fig)
        assert f"Total ({PowerSpectrumBPL.SHORT_NAME})" in labels(fig)

    @staticmethod
    def test_no_spectra():
        """Drawing without spectra should fail with a clear error."""
        with pytest.raises(ValueError, match="no power spectra"):
            power_spectrum_figure([])
