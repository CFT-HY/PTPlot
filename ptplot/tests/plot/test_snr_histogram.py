"""Tests for the SNR histograms."""

from django.test import TestCase
from matplotlib.patches import Polygon
import numpy as np
import pytest

from ptplot.science import const
from ptplot.science.plot.snr_histogram import N_BINS_MIN, snr_histogram, snr_histogram_figure
from ptplot.science.snr import snr_point, snr_points
from ptplot.science.spectrum import Engine
from ptplot.science.spectrum.engines import ENGINE_NAMES
from ptplot.science.spectrum.ssm import SSMSettings
from ptplot.tests.const import TEST_SSM_SETTINGS

#: Parameters of the test points. The last point has an invalid wall velocity, and therefore its SNR is NaN.
V_WALL: np.ndarray = np.array([0.5, 0.9, 0.7, 1.5])
ALPHA_N: np.ndarray = np.array([0.05, 0.1, 0.3, 0.1])
BETA_TILDE: np.ndarray = np.array([100., 1000., 10., 100.])
T_STAR: np.ndarray = np.array([const.DEFAULT_T_STAR, 50., 200., const.DEFAULT_T_STAR])
G_STAR: np.ndarray = np.array([const.DEFAULT_G_STAR, 100., 110., const.DEFAULT_G_STAR])
#: Engines of the tests, including the SSM, which is computed in parallel
ENGINES: list[Engine] = [Engine.CosWG20bpl, Engine.GH21dbpl, Engine.SSM]


def points(
        engines: list[Engine] = ENGINES,
        n_points: int = V_WALL.size,
        max_workers: int = 2,
        ssm_settings: SSMSettings | None = TEST_SSM_SETTINGS) -> np.ndarray:
    """Compute the SNR values of the first test points."""
    return snr_points(
        v_wall=V_WALL[:n_points], alpha_n=ALPHA_N[:n_points], beta_tilde=BETA_TILDE[:n_points],
        T_star=T_STAR[:n_points], g_star=G_STAR[:n_points],
        engines=engines, ssm_settings=ssm_settings, max_workers=max_workers
    )


class SNRPointsTest(TestCase):
    """Tests for :py:func:`ptplot.science.snr.points.snr_points`."""

    @staticmethod
    def test_serial() -> None:
        """The SNR values computed in parallel should be those of the points computed one by one."""
        snr = points()
        assert snr.shape == (V_WALL.size, len(ENGINES))
        for i_engine, engine in enumerate(ENGINES):
            for i_point in range(V_WALL.size):
                reference, _, _ = snr_point(
                    x=ALPHA_N[i_point], y=BETA_TILDE[i_point], T_star=T_STAR[i_point], g_star=G_STAR[i_point],
                    v_wall=V_WALL[i_point], noise=None, engine=engine, parallel=False, ssm_settings=TEST_SSM_SETTINGS,
                    legacy_nucleation_cs_max=const.DEFAULT_LEGACY_NUCLEATION_CS_MAX
                )
                np.testing.assert_allclose(snr[i_point, i_engine], reference, rtol=1e-12, atol=0)
        # The invalid point fails with every engine, and the others succeed.
        assert np.all(np.isnan(snr[-1]))
        assert np.all(np.isfinite(snr[:-1]))

    @staticmethod
    def test_workers() -> None:
        """The SNR values should not depend on the number of workers."""
        np.testing.assert_array_equal(points(max_workers=1), points(max_workers=3))


def test_histogram_figure() -> None:
    """The engines should be in the legend with the numbers of points if not all points were solved."""
    snr = np.array([[1., 2.], [10., np.inf], [100., np.nan]])
    engines = [Engine.CosWG20bpl, Engine.GH21dbpl]
    fig = snr_histogram_figure(snr, engines)
    legend = fig.get_axes()[0].get_legend()
    assert legend is not None
    # Matplotlib lists the datasets of a histogram in the reverse order in the legend.
    assert sorted(text.get_text() for text in legend.get_texts()) == sorted([
        f"{ENGINE_NAMES[Engine.CosWG20bpl]}, n=3", f"{ENGINE_NAMES[Engine.GH21dbpl]}, n=1"
    ])
    # The input is not modified.
    assert np.isinf(snr[1, 1])


def test_histogram() -> None:
    """The histogram should be drawn from the SNR values of the points."""
    fig = snr_histogram(
        v_wall=V_WALL[:-1], alpha_n=ALPHA_N[:-1], beta_tilde=BETA_TILDE[:-1], T_star=T_STAR[:-1], g_star=G_STAR[:-1],
        engines=ENGINES[:2]
    )
    legend = fig.get_axes()[0].get_legend()
    assert legend is not None
    labels = sorted(text.get_text() for text in legend.get_texts())
    assert labels == sorted(ENGINE_NAMES[engine] for engine in ENGINES[:2])


def test_histogram_bins() -> None:
    """The number of bins should follow from the number of points if the SNR values span only a few decades."""
    snr = np.linspace(1, 10, 200)[:, np.newaxis]
    engines = [Engine.CosWG20bpl]

    def n_bins(**kwargs: int) -> int:
        # The edges of the bins of the step histogram are the vertices of its patch.
        patch = snr_histogram_figure(snr, engines, **kwargs).get_axes()[0].patches[0]
        assert isinstance(patch, Polygon)
        return np.unique(patch.get_xy()[:, 0]).size - 1

    assert n_bins() == 200 // 10
    assert n_bins(points_per_bin=50) == N_BINS_MIN
    n_bins_min = N_BINS_MIN + 3
    assert n_bins(points_per_bin=50, n_bins_min=n_bins_min) == n_bins_min


@pytest.mark.parametrize(("log10_min", "log10_max", "edges"), [
    (0.5, 7.5, (0, 8)),
    # The values below 1 have negative logarithms, which are rounded down as well.
    (-2.5, 4.5, (-3, 5)),
    # A whole decade at the end is not extended, as the last bin includes its upper edge.
    (-3., 4., (-3, 4)),
])
def test_histogram_bins_decades(log10_min: float, log10_max: float, edges: tuple[int, int]) -> None:
    """If the SNR values span more decades than the minimum number of bins, there should be a bin for each decade.

    All the values should be within the bins.
    """
    snr = np.logspace(log10_min, log10_max, 200)[:, np.newaxis]
    patch = snr_histogram_figure(snr, [Engine.CosWG20bpl]).get_axes()[0].patches[0]
    assert isinstance(patch, Polygon)
    bin_edges = np.unique(patch.get_xy()[:, 0])
    np.testing.assert_allclose(np.log10(bin_edges), np.arange(edges[0], edges[1] + 1), atol=1e-12)
    assert np.histogram(snr, bins=bin_edges)[0].sum() == snr.size
