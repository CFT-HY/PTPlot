"""Tests for the form of the axes of the SNR grids."""

from django.test import TestCase

from ptplot.forms import GridAxesForm
from ptplot.science import const
from ptplot.science.snr.grid import GridAxes


class GridAxesFormTest(TestCase):
    """Tests for the size and limits of the axes of the SNR grids."""

    @staticmethod
    def test_defaults() -> None:
        """Without data the default axes should be used."""
        form = GridAxesForm({})
        assert form.is_valid(), form.errors
        assert form.axes == GridAxes()

    @staticmethod
    def test_axes() -> None:
        """The given size and limits should be used."""
        form = GridAxesForm({"grid_size": "5", "beta_tilde_min": "10", "beta_tilde_max": "1000", "r_star_max": "0.1"})
        assert form.is_valid(), form.errors
        assert form.axes == GridAxes(size=5, beta_tilde_min=10., beta_tilde_max=1000., r_star_max=0.1)

    @staticmethod
    def test_invalid() -> None:
        """Sizes outside the allowed range and ranges that are not positive and increasing should be rejected."""
        for data in (
                {"grid_size": const.DEFAULT_GRID_SIZE + 1},
                {"grid_size": 1},
                {"alpha_min": 0},
                {"alpha_min": 0.5, "alpha_max": 0.1},
                # Above the maximum of the default range
                {"beta_tilde_min": 1e6},
                # Below the minimum of the default range
                {"r_star_max": 1e-5}):
            form = GridAxesForm(data)
            assert not form.is_valid(), data
