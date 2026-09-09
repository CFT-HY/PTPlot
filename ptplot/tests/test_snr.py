"""Tests for the SNR grids and their comparisons."""

from django.test import TestCase
from matplotlib.colors import SymLogNorm
import numpy as np
import pytest

from ptplot.science import const
from ptplot.science.plot.snr_alpha_beta import snr_figure_alpha_beta
from ptplot.science.plot.snr_comparison import snr_comparison
from ptplot.science.plot.snr_ubarf_rstar import snr_figure_ubarf_rstar
from ptplot.science.snr.grid_alpha_beta import SNRGridAlphaBeta
from ptplot.science.snr.grid_comparison import ComparisonMethod, SNRGridComparison
from ptplot.science.snr.grid_ubarf_rstar import SNRGridUbarfRStar


class SNRTest(TestCase):
    """Tests for the SNR grids and their comparisons."""

    @staticmethod
    def test_snr_alpha_beta():
        snr_figure_alpha_beta(
            grid=SNRGridAlphaBeta(
                T_star=const.DEFAULT_T_STAR, g_star=const.DEFAULT_G_STAR, v_wall=const.DEFAULT_V_WALL,
                alpha_points=const.DEFAULT_ALPHA, beta_over_H_points=const.DEFAULT_BETA_OVER_H,
                v_wall_points=const.DEFAULT_V_WALL
            )
        )

    @staticmethod
    def test_snr_ubarf_rstar():
        snr_figure_ubarf_rstar(
            grid=SNRGridUbarfRStar(
                T_star=const.DEFAULT_T_STAR, g_star=const.DEFAULT_G_STAR, v_wall=const.DEFAULT_V_WALL,
                alpha_points=const.DEFAULT_ALPHA, beta_over_H_points=const.DEFAULT_BETA_OVER_H,
                v_wall_points=const.DEFAULT_V_WALL
            )
        )

    @staticmethod
    def snr_grid(name: str | None = None) -> SNRGridAlphaBeta:
        """Create a small SNR grid for the comparison tests."""
        return SNRGridAlphaBeta(
            T_star=const.DEFAULT_T_STAR, g_star=const.DEFAULT_G_STAR, v_wall=const.DEFAULT_V_WALL,
            alpha_n=np.array([0.1, 1.]), beta_over_H=np.array([100., 1000.]),
            alpha_points=const.DEFAULT_ALPHA, beta_over_H_points=const.DEFAULT_BETA_OVER_H,
            v_wall_points=const.DEFAULT_V_WALL,
            name=name
        )

    @classmethod
    def snr_grids(cls) -> tuple[SNRGridAlphaBeta, SNRGridAlphaBeta]:
        """Create two grids with known SNR values."""
        grid1 = cls.snr_grid(name="grid1")
        grid2 = cls.snr_grid(name="grid2")
        grid1.snr = np.array([[1., 10.], [100., 1000.]])
        grid2.snr = np.array([[2., 5.], [100., 0.]])
        return grid1, grid2

    @classmethod
    def test_snr_comparison_relative(cls):
        grid1, grid2 = cls.snr_grids()
        comparison = SNRGridComparison(grid1=grid1, grid2=grid2)

        assert comparison.method == ComparisonMethod.RELATIVE_DIFFERENCE
        assert not comparison.logarithmic
        np.testing.assert_allclose(comparison.snr_diff, np.array([[0.5, -0.5], [0., -1.]]))
        # The levels and the color scale are chosen by Matplotlib.
        assert comparison.levels is None
        assert comparison.norm is None
        assert comparison.label == (
            r"$\frac{\text{SNR}_{grid2} - \text{SNR}_{grid1}}"
            r"{\max( \text{SNR}_{grid1}, \text{SNR}_{grid2} )}$"
        )
        snr_comparison(comparison)

    @classmethod
    def test_snr_comparison_absolute(cls):
        grid1, grid2 = cls.snr_grids()
        comparison = SNRGridComparison(
            grid1=grid1, grid2=grid2,
            method=ComparisonMethod.ABSOLUTE_DIFFERENCE,
            n_decades=6
        )

        assert comparison.logarithmic
        np.testing.assert_allclose(comparison.snr_diff, np.array([[1., -5.], [0., -1000.]]))
        levels = comparison.levels
        assert levels is not None
        positive = np.logspace(-3, 3, 7)
        np.testing.assert_allclose(levels, np.concatenate((-positive[::-1], np.zeros(1), positive)))
        norm = comparison.norm
        assert isinstance(norm, SymLogNorm)
        np.testing.assert_allclose(norm.linthresh, 1e-3)
        assert comparison.label == r"$\text{SNR}_{grid2} - \text{SNR}_{grid1}$"
        snr_comparison(comparison)

    @classmethod
    def test_snr_comparison_axes(cls):
        """The comparison provides the axes of the grids."""
        grid1, grid2 = cls.snr_grids()
        comparison = SNRGridComparison(grid1=grid1, grid2=grid2)

        np.testing.assert_allclose(comparison.x, grid1.x)
        np.testing.assert_allclose(comparison.y, grid1.y)
        assert comparison.X_NAME == grid1.X_NAME
        assert comparison.Y_NAME == grid1.Y_NAME
        assert comparison.X_LABEL == grid1.X_LABEL
        assert comparison.Y_LABEL == grid1.Y_LABEL

    @classmethod
    def test_snr_comparison_label(cls):
        """A label given by the user overrides the automatic one."""
        grid1, grid2 = cls.snr_grids()
        assert SNRGridComparison(grid1=grid1, grid2=grid2, label="custom").label == "custom"

    @classmethod
    def test_snr_comparison_identical(cls):
        """Identical grids cannot be drawn on a logarithmic scale, so a linear one is used."""
        grid = cls.snr_grid()
        comparison = SNRGridComparison(
            grid1=grid, grid2=grid,
            method=ComparisonMethod.ABSOLUTE_DIFFERENCE
        )
        assert comparison.levels is None
        assert comparison.norm is None
        snr_comparison(comparison)

    @classmethod
    def test_snr_comparison_invalid(cls):
        """Grids with different ranges cannot be compared."""
        grid2 = SNRGridAlphaBeta(
            T_star=const.DEFAULT_T_STAR, g_star=const.DEFAULT_G_STAR, v_wall=const.DEFAULT_V_WALL,
            alpha_n=np.array([0.1, 2.]), beta_over_H=np.array([100., 1000.]),
            alpha_points=const.DEFAULT_ALPHA, beta_over_H_points=const.DEFAULT_BETA_OVER_H,
            v_wall_points=const.DEFAULT_V_WALL
        )
        with pytest.raises(ValueError, match="same ranges"):
            SNRGridComparison(grid1=cls.snr_grid(), grid2=grid2)
