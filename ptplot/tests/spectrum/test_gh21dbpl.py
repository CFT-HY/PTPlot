"""Double broken power law (DBPL) tests (2021 version)."""

import unittest

import numpy as np
from pttools.omgw0.const import H
import pytest

from ptplot.science.spectrum.gh21dbpl import GH21dbpl, GH21dbplParams, M, ssm_fit
from ptplot.tests.spectrum.coswg20 import PowerSpectrumBaseCase2020

#: Best-fit $\hat{\Omega}_p$, $z_b$, $z_p$, $b$ and $\delta_\mathcal{P}^2$ of :gowling_2021:`\ ` at the grid indices
#: ``[alpha_n, v_wall]``, from ``fit_dbl_brkn_4_pgw16_11_20_params50_51_log_alpha_vw_correction.npz``
#: of the ``fisher_analysis`` repository of :gowling_2021:`\ `.
GOWLING_FIT: dict[tuple[int, int], tuple[float, ...]] = {
    (0, 0): (
        5.2828694423021445e-09, 1.1656667399929075, 3.1763165163571916, 0.7626226299312603, 0.0032512257168008252
    ),
    (20, 25): (
        9.458890564612797e-07, 1.3819073805435742, 27.043578172105484, 0.5306149024642237, 0.009422704599236963
    ),
    (30, 10): (
        3.1976474541843646e-05, 1.2529181934052616, 5.187119183142538, 0.7619822335529763, 0.0030340173527730065
    ),
    (49, 50): (
        0.00044175567406300073, 1.512222010168032, 3.8199433411316304, -0.12858555199189156, 0.03192396535369428
    ),
}


class DBPL2021Test(PowerSpectrumBaseCase2020[GH21dbpl], unittest.TestCase):
    """Tests for the double broken power law (DBPL) power spectrum of 2021."""

    SPECTRUM_CLASS = GH21dbpl
    # Within the range of the SSM fit
    V_WALL = 0.6

    def test_fit_gowling(self) -> None:
        r"""The SSM fit should reproduce the fit of :gowling_2021:`\ `."""
        fit = ssm_fit()
        for (i, j), (omp, zb, zp, b, delta2) in GOWLING_FIT.items():
            assert fit.omega_p_hat[i, j] == pytest.approx(omp, rel=1e-3)
            assert fit.zb[i, j] == pytest.approx(zb, rel=1e-3)
            assert fit.zp[i, j] == pytest.approx(zp, rel=1e-3)
            assert fit.b[i, j] == pytest.approx(b, rel=1e-3)
            assert fit.delta2[i, j] == pytest.approx(delta2, rel=1e-3)

    def test_fit_quality(self) -> None:
        r"""The DBPL should fit the SSM well, :gowling_2021:`\ ` fig. 11."""
        assert np.median(ssm_fit().delta2) < 0.05  # noqa: PLR2004

    def test_interpolate_grid_point(self) -> None:
        """The interpolation should reproduce the fit at the grid points."""
        fit = ssm_fit()
        i, j = 20, 25
        assert fit.interpolate(v_wall=fit.v_walls[j], alpha_n=fit.alpha_ns[i]) == pytest.approx(
            (fit.omega_p_hat[i, j], fit.zb[i, j], fit.zp[i, j], fit.b[i, j]), rel=1e-12
        )

    def test_interpolate_outside(self) -> None:
        """Points outside the grid should give a warning and use the closest edge."""
        fit = ssm_fit()
        with pytest.warns(UserWarning, match="outside the grid"):
            outside = fit.interpolate(v_wall=0.3, alpha_n=1.)
        assert outside == pytest.approx(fit.interpolate(v_wall=fit.v_walls[0], alpha_n=fit.alpha_ns[-1]))

    def test_J(self) -> None:
        r"""$J$ should be that of :gowling_2021:`\ ` eq. 2.7, 2.8."""
        # K from calc_ke_frac(0.6, 0.1) of Ke_frac.py of the fisher_analysis repository
        K = 0.03690783215418014
        spectrum = GH21dbpl(v_wall=0.6, alpha=0.1, r_star=0.1)
        assert spectrum.kinetic_energy_fraction == pytest.approx(K, rel=1e-12)
        assert spectrum.J() == pytest.approx(0.1 * (1 - (1 + 2 * 0.1 / np.sqrt(K))**-0.5), rel=1e-12)

    def test_legacy(self) -> None:
        """The legacy version should reproduce the earlier PTPlot version."""
        spectrum = GH21dbpl.cached(
            T_star=100, g_star=100, v_wall=0.7, alpha=0.2, r_star=0.1, zb=2.0, zp=20., legacy=True
        )
        assert spectrum.power_spectrum(np.array([1e-4, 1e-3, 1e-2]))[0] == pytest.approx(
            [8.698178327992318e-12, 2.0494010535202413e-11, 1.2769992262503812e-14], rel=1e-12
        )

    def test_M_peak(self) -> None:
        r"""$M(s)$ should have its maximum $M(1) = 1$ at $s = 1$ for $r_b < 1$, :gowling_2021:`\ ` p. 9."""
        s = np.logspace(-2, 2, 4001)
        for rb, b in ((0.1, 1.), (0.5, 0.5), (0.9, -0.5)):
            assert M(s=1., rb=rb, b=b) == pytest.approx(1, rel=1e-14)
            assert s[np.argmax(M(s=s, rb=rb, b=b))] == pytest.approx(1, rel=1e-12)

    def test_omega_peak(self) -> None:
        r"""The spectrum should peak at $f_p$ with the value $\Omega_{p,0}$, :gowling_2021:`\ ` eq. 2.18."""
        spectrum = self.spectrum
        assert spectrum.omega_peak_h2() == pytest.approx(
            spectrum.F_gw0_h2() * spectrum.J() * spectrum.omega_p_hat * spectrum.suppression_factor, rel=1e-14
        )
        f_peak = spectrum.f_peak()
        power, _ = spectrum.power_spectrum(np.array([f_peak]))
        assert power[0] == pytest.approx(spectrum.omega_peak_h2(), rel=1e-12)

    def test_params(self) -> None:
        """The parameters on a grid should be those of the individual spectra."""
        v_walls = np.array([0.5, 0.7])
        alpha_ns = np.array([0.05, 0.1, 0.2])
        params = GH21dbplParams.compute(v_walls=v_walls, alpha_ns=alpha_ns, r_star=0.1, T_star=100, g_star=100)
        assert params.omega_p0_h2.shape == (alpha_ns.size, v_walls.size)
        spectrum = GH21dbpl(v_wall=0.7, alpha=0.1, r_star=0.1, T_star=100, g_star=100)
        assert params.omega_p0_h2[1, 1] == pytest.approx(spectrum.omega_peak_h2(), rel=1e-14)
        assert params.omega_p0[1, 1] == pytest.approx(spectrum.omega_peak_h2() / H**2, rel=1e-14)
        assert params.f_p0[1, 1] == pytest.approx(spectrum.f_peak(), rel=1e-14)
        assert params.rb[1, 1] == pytest.approx(spectrum.rb, rel=1e-14)
        assert params.b[1, 1] == pytest.approx(spectrum.b, rel=1e-14)

    def test_requires_v_wall(self) -> None:
        r"""The SSM fit requires $v_{\text{wall}}$."""
        with pytest.raises(ValueError, match="requires v_wall"):
            GH21dbpl(alpha=0.1, r_star=0.1)
