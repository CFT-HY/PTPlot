"""Tests for the power spectrum figure."""

from django.test import TestCase
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
import pytest

from ptplot.science import const
from ptplot.science.plot.ps import power_spectrum_figure
from ptplot.science.spectrum import (
    CosWG20bpl,
    CosWG24bpl,
    CosWG24dbpl,
    GH21dbpl,
    PowerSpectrum,
)

#: Engines that are quick enough to be drawn in the tests. The SSM is excluded, as it's slow.
SPECTRUM_CLASSES: tuple[type[PowerSpectrum], ...] = (
    CosWG20bpl, CosWG24bpl, GH21dbpl, CosWG24dbpl
)


def spectra() -> list[PowerSpectrum]:
    """Create one power spectrum of each engine that is tested."""
    return [
        spectrum_class.cached(
            v_wall=const.DEFAULT_V_WALL, alpha=const.DEFAULT_ALPHA, beta_tilde=const.DEFAULT_BETA_TILDE
        )
        for spectrum_class in SPECTRUM_CLASSES
    ]


def labels(fig: Figure, strip_snr: bool = True) -> list[str]:
    """Get the legend labels of the curves of a figure.

    :param fig: Figure
    :param strip_snr: Remove the SNR values from the labels, as they depend on the spectra
    :return: Legend labels
    """
    return [
        label.split(", SNR=")[0] if strip_snr else label
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
    def test_single() -> None:
        """A single spectrum should be drawn with its engine in the legend."""
        spectrum = spectra()[0]
        fig = power_spectrum_figure(spectrum)
        assert labels(fig) == [rf"$\Omega_\mathrm{{sw}}$ ({spectrum.SHORT_NAME})"]

    @staticmethod
    def test_multiple() -> None:
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
    def test_title() -> None:
        """The title should be drawn above the axes and the text, and fit in the figure."""
        title = "Test title"
        fig = power_spectrum_figure(spectra(), title=title)
        ax = fig.get_axes()[0]
        assert ax.get_title() == title
        renderer = FigureCanvasAgg(fig).get_renderer()
        title_extent = ax.title.get_window_extent(renderer)
        text_extent = ax.texts[0].get_window_extent(renderer)
        assert title_extent.y0 >= text_extent.y1
        assert title_extent.y1 <= fig.bbox.y1

    @staticmethod
    def test_no_title() -> None:
        """There should be no title by default."""
        assert power_spectrum_figure(spectra()).get_axes()[0].get_title() == ""

    @staticmethod
    def test_multiple_with_turbulence() -> None:
        """Each component of each spectrum should be drawn with its engine in the legend."""
        spectra_list = spectra()
        fig = power_spectrum_figure(spectra_list, sw_only=False)
        for spectrum in spectra_list:
            assert rf"$\Omega_\mathrm{{sw}}$ ({spectrum.SHORT_NAME})" in labels(fig)
        # Only the BPL has turbulence curves.
        assert rf"$\Omega_\mathrm{{turb}}$ ({CosWG20bpl.SHORT_NAME})" in labels(fig)
        assert f"Total ({CosWG20bpl.SHORT_NAME})" in labels(fig)

    @staticmethod
    def test_no_spectra() -> None:
        """Drawing without spectra should fail with a clear error."""
        with pytest.raises(ValueError, match="no power spectra"):
            power_spectrum_figure([])
