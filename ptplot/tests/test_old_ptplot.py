r"""Comparison of the SNR grids with the last version of PTPlot before the restructuring.

The tests use :py:mod:`ptplot.tests.old_ptplot` to find the old PTPlot, and are skipped if it is not found.
The constant factors between the old and the new SNR are removed before the comparison
(please see :py:mod:`ptplot.tests.old_ptplot`).

The old noise curves use the low-frequency approximation of the LISA response.
With the exact response of :py:func:`pttools.omgw0.noise.omega_noise_h2`, the SNR of spectra that peak
above a few mHz is larger than the old one (by up to a third at $r_* = 10^{-4}$).
Therefore, the grid is compared with the exact noise only for large $r_*$,
and with the approximate response :py:func:`pttools.omgw0.noise.S_AE_approx` over the whole grid.
The compact binary noises are disabled, as the old curves do not have them.
"""

import unittest

from django.test import TestCase
import numpy as np

from ptplot.science import const
from ptplot.science.noise import Noise
from ptplot.science.snr.grid_alpha_beta import SNRGridAlphaBeta
from ptplot.science.snr.grid_ubarf_rstar import SNRGridUbarfRStar
from ptplot.science.spectrum.engine import Engine
import ptplot.science.type_hints as th
from ptplot.tests.old_ptplot import (
    HAVE_OLD_PTPLOT,
    NOT_FOUND_MESSAGE,
    OLD_OBS_YEARS,
    OLD_UBARF_MAX_ALPHA_BETA,
    approx_noise,
    exact_noise,
    old_grid,
    old_modules,
    reconstructed_old_grid,
    snr_factor,
)

#: Parameters of the comparison
T_STAR: float = 100.
G_STAR: float = 100.
#: Ratio of the new and the old SNR, when the only differences are the constant factors
SNR_FACTOR: float = snr_factor(G_STAR)
#: Relative tolerance of :py:func:`ptplot.tests.old_ptplot.reconstructed_old_grid`
RTOL_RECONSTRUCTED: float = 1e-3

#: With the exact response, the grid is compared only for spectra that peak well below the transfer frequency
R_STAR_MIN_EXACT: float = 1e-2
#: Relative tolerance with the exact response, set by the high-frequency tail of the spectra at $r_* = 10^{-2}$
RTOL_EXACT: float = 1e-2
#: Relative tolerance with the approximate response, set by the transfer frequency
#: $f_2 = 25 \ \text{mHz}$ vs. $25.45 \ \text{mHz}$ (please see :py:mod:`ptplot.tests.test_noise`)
RTOL_APPROX: float = 1.5e-2
#: Relative tolerance of the $\bar{U}_f \rightarrow \alpha$ inversion of the old code,
#: which is solved with an absolute tolerance of $10^{-6}$
RTOL_ALPHA_BETA: float = 2e-2
#: Minimum relative difference from the old grid for $v_{\text{wall}} < c_s$ without the legacy conversion
MIN_DIFFERENCE_DEFLAGRATION: float = 0.5


def new_grid_ubarf_rstar(noise: Noise) -> SNRGridUbarfRStar:
    r"""Compute the SNR grid of BPL2020 on the default $(\bar{U}_f, r_*)$ grid of the old code."""
    return SNRGridUbarfRStar(
        v_wall=const.DEFAULT_V_WALL, T_star=T_STAR, g_star=G_STAR,
        ubarf=const.DEFAULT_UBARF_RANGE, r_star=const.DEFAULT_R_STAR_RANGE,
        noise=noise, engine=Engine.BPL2020, log_progress_percentage=None
    )


@unittest.skipUnless(HAVE_OLD_PTPLOT, NOT_FOUND_MESSAGE)
class OldPTPlotUbarfRStarTest(TestCase):
    r"""Compare the $(\bar{U}_f, r_*)$ SNR grid of BPL2020 with the old PTPlot."""

    @staticmethod
    def test_grid_ranges():
        """The default grid should still be that of the old code."""
        _, _, log10_r_star, log10_ubarf = old_grid(T_STAR, G_STAR)
        np.testing.assert_allclose(10**log10_r_star, const.DEFAULT_R_STAR_RANGE, rtol=1e-12)
        np.testing.assert_allclose(10**log10_ubarf, const.DEFAULT_UBARF_RANGE, rtol=1e-12)

    @staticmethod
    def test_shock_times():
        r"""The shock times $H_* \tau_\text{sh} = r_* / \bar{U}_f$ do not depend on the noise."""
        shock_times, _, _, _ = old_grid(T_STAR, G_STAR)
        np.testing.assert_allclose(new_grid_ubarf_rstar(exact_noise()).shock_times, shock_times, rtol=1e-12)

    @staticmethod
    def test_snr_exact_noise():
        """With the exact response, the SNR should match for spectra that peak at low frequencies."""
        _, snr_old, log10_r_star, _ = old_grid(T_STAR, G_STAR)
        rows = 10**log10_r_star >= R_STAR_MIN_EXACT
        snr_new = new_grid_ubarf_rstar(exact_noise()).snr
        np.testing.assert_allclose(snr_new[rows] / SNR_FACTOR, snr_old[rows], rtol=RTOL_EXACT)

    @staticmethod
    def test_snr_approx_noise():
        """With the approximate response, the SNR should match over the whole grid."""
        _, snr_old, _, _ = old_grid(T_STAR, G_STAR)
        snr_new = new_grid_ubarf_rstar(approx_noise()).snr
        np.testing.assert_allclose(snr_new / SNR_FACTOR, snr_old, rtol=RTOL_APPROX)

    @staticmethod
    def test_snr_ratio_depends_only_on_r_star():
        r"""The noise changes the SNR by a factor that depends on $r_*$ but not on $\bar{U}_f$.

        This is why the new noise curves change the shape of the SNR contours
        but not the BPL2020 spectrum itself.
        """
        _, snr_old, _, _ = old_grid(T_STAR, G_STAR)
        ratio = new_grid_ubarf_rstar(Noise(obs_years=OLD_OBS_YEARS)).snr / snr_old
        np.testing.assert_allclose(ratio, np.repeat(ratio[:, :1], ratio.shape[1], axis=1), rtol=1e-10)

    @staticmethod
    def test_reconstructed():
        """The reconstruction of the old grid with the new code should match the old code."""
        for ubarf_max in (1., OLD_UBARF_MAX_ALPHA_BETA):
            shock_times, snr, log10_r_star, log10_ubarf = old_grid(T_STAR, G_STAR, ubarf_max)
            shock_times2, snr2, log10_r_star2, log10_ubarf2 = reconstructed_old_grid(T_STAR, G_STAR, ubarf_max)
            np.testing.assert_allclose(log10_r_star2, log10_r_star, rtol=1e-12)
            np.testing.assert_allclose(log10_ubarf2, log10_ubarf, rtol=1e-12)
            np.testing.assert_allclose(shock_times2, shock_times, rtol=1e-12)
            np.testing.assert_allclose(snr2, snr, rtol=RTOL_RECONSTRUCTED)

    @staticmethod
    def test_points_legacy():
        r"""With the legacy $\max(v_{\text{wall}}, c_s)$, the points should be converted as in the old code."""
        old = old_modules()
        v_wall = 0.3
        alpha = np.array([0.05, 0.1, 0.3])
        beta_tilde = np.array([30., 100., 1000.])
        for legacy in (True, False):
            grid = SNRGridUbarfRStar(
                v_wall=v_wall, T_star=T_STAR, g_star=G_STAR,
                alpha_points=alpha, beta_tilde_points=beta_tilde, v_wall_points=np.full_like(alpha, v_wall),
                ubarf=const.DEFAULT_UBARF_RANGE, r_star=const.DEFAULT_R_STAR_RANGE,
                noise=exact_noise(), engine=Engine.BPL2020, log_progress_percentage=None,
                legacy_nucleation_cs_max=legacy
            )
            ubarf_points, r_star_points = grid.points()
            np.testing.assert_allclose(
                np.asarray(ubarf_points).ravel(), [old.espinosa.ubarf(v_wall, a) for a in alpha], rtol=1e-12
            )
            r_star_old = np.array([old.calculate_powerspectrum.beta_to_rstar(b, v_wall) for b in beta_tilde])
            r_star_expected = r_star_old if legacy else r_star_old * v_wall / const.CS0
            np.testing.assert_allclose(np.asarray(r_star_points).ravel(), r_star_expected, rtol=1e-12)


@unittest.skipUnless(HAVE_OLD_PTPLOT, NOT_FOUND_MESSAGE)
class OldPTPlotAlphaBetaTest(TestCase):
    r"""Compare the $(\alpha, \beta/H_*)$ SNR grid of BPL2020 with the old PTPlot.

    The old code computed the grid on the $(\bar{U}_f, r_*)$ plane and converted the axes to $(\alpha, \beta/H_*)$
    (``SNRalphabeta_onthefly.py``). Here the new grid is computed on those converted axes,
    so that the grids can be compared point by point.
    """

    @classmethod
    def old_axes(cls, v_wall: float) -> tuple[th.FloatArr1D, th.FloatArr1D]:
        r"""Get the $\alpha$ and $\beta/H_*$ axes of the old figure."""
        old = old_modules()
        _, _, log10_r_star, log10_ubarf = old_grid(T_STAR, G_STAR, OLD_UBARF_MAX_ALPHA_BETA)
        alpha = old.espinosa.ubarf_to_alpha(v_wall, 10**log10_ubarf)
        beta_tilde = np.array([old.calculate_powerspectrum.rstar_to_beta(10**r, v_wall) for r in log10_r_star])
        return alpha, beta_tilde

    @classmethod
    def new_snr(cls, v_wall: float, legacy: bool) -> th.FloatArr2D:
        alpha, beta_tilde = cls.old_axes(v_wall)
        return SNRGridAlphaBeta(
            T_star=T_STAR, g_star=G_STAR, v_wall=v_wall,
            alpha_n=alpha, beta_tilde=beta_tilde,
            noise=approx_noise(), engine=Engine.BPL2020, log_progress_percentage=None,
            legacy_nucleation_cs_max=legacy
        ).snr

    def check(self, v_wall: float, legacy: bool) -> None:
        _, snr_old, _, _ = old_grid(T_STAR, G_STAR, OLD_UBARF_MAX_ALPHA_BETA)
        np.testing.assert_allclose(
            self.new_snr(v_wall, legacy) / SNR_FACTOR, snr_old, rtol=RTOL_ALPHA_BETA,
            err_msg=f"v_wall={v_wall}, legacy_nucleation_cs_max={legacy}"
        )

    def test_detonation(self):
        r"""For $v_{\text{wall}} > c_s$ the conversion does not depend on the legacy option."""
        for legacy in (True, False):
            self.check(v_wall=0.9, legacy=legacy)

    def test_deflagration_legacy(self):
        r"""For $v_{\text{wall}} < c_s$ the legacy option should reproduce the old grid."""
        self.check(v_wall=0.3, legacy=True)

    def test_deflagration_default(self):
        r"""For $v_{\text{wall}} < c_s$ the default conversion should differ from the old grid.

        The default $r_*$ is smaller by the factor $v_{\text{wall}} / c_s$.
        """
        v_wall = 0.3
        _, snr_old, _, _ = old_grid(T_STAR, G_STAR, OLD_UBARF_MAX_ALPHA_BETA)
        ratio = self.new_snr(v_wall, legacy=False) / SNR_FACTOR / snr_old
        assert np.nanmax(np.abs(ratio - 1)) > MIN_DIFFERENCE_DEFLAGRATION, \
            "The default conversion should differ from the old one."
