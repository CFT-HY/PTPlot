r"""Broken power law (BPL) tests (2024 version).

The equation and page numbers refer to :caprini_2024:`\ ` arXiv:2403.03723v2.
"""

import unittest

import numpy as np
import pytest

from ptplot.science.spectrum.bpl2024 import PowerSpectrumBPL2024
from ptplot.tests.spectrum.base_spectrum import PowerSpectrumBaseCase

#: Reference values of $h^2 \Omega_p$, $f_p$ and $h^2 \Omega_{\text{gw}}(f_p / 10)$
#: for the default parameters of :func:`spectrum`, from the first implementation
REFERENCE = np.array([6.826356098972105e-11, 0.00018150000000000002, 3.4042341173288775e-12])


class BPL2024Test(PowerSpectrumBaseCase, unittest.TestCase):
    """Tests for the broken power law (BPL) power spectrum of 2024."""

    SPECTRUM_CLASS = PowerSpectrumBPL2024


class AsymmetricBPL2024(PowerSpectrumBPL2024):
    r"""BPL2024 with $n_1 \neq -n_2$, for which $f_b \neq f_p$ and $\Omega_b \neq \Omega_p$."""

    SLOPES = (3., -1.)
    SMOOTHNESS = (2.,)


def spectrum(
        alpha: float = 10., beta_tilde: float = 100.,
        cls: type[PowerSpectrumBPL2024] = PowerSpectrumBPL2024) -> PowerSpectrumBPL2024:
    """Create a BPL2024 spectrum with $T_* = 100$ GeV and $g_* = 100$."""
    return cls(T_star=100, g_star=100, v_wall=0.95, alpha=alpha, beta_tilde=beta_tilde)


def test_peak():
    r"""$f_p = 0.11 H_{\ast,0} \beta / H_*$, eq. 2.2 and 2.7."""
    assert spectrum(beta_tilde=100).f_peak() == pytest.approx(0.11 * 1.65e-5 * 100)


def test_omega_p():
    r"""$h^2 \Omega_p = h^2 F_{\text{gw},0} A_{\text{str}} \tilde{K}^2 (H_*/\beta)^2$, eq. 2.7."""
    spec = spectrum(alpha=10, beta_tilde=100)
    k_tilde = 10 / 11
    assert spec.K_tilde == pytest.approx(k_tilde)
    assert spec.omega_p_h2() == pytest.approx(spec.F_gw0_h2() * 0.05 * k_tilde**2 / 100**2, rel=1e-12)


def test_symmetric_slopes():
    r"""$f_b = f_p$ and $\Omega_b = \Omega_p$ for $n_1 = -n_2$, p. 8."""
    spec = spectrum()
    assert spec.f_b() == pytest.approx(spec.f_peak())
    assert spec.omega_b_h2() == pytest.approx(spec.omega_p_h2())


@pytest.mark.parametrize("cls", [PowerSpectrumBPL2024, AsymmetricBPL2024])
def test_peak_consistency(cls: type[PowerSpectrumBPL2024]):
    r"""The spectrum should have its maximum $\Omega_p$ at $f_p$, eq. 2.4-2.6."""
    spec = spectrum(cls=cls)
    f_peak = spec.f_peak()
    assert spec.f_peak_numerical() == pytest.approx(f_peak, rel=1e-8)
    ps, _ = spec.power_spectrum(f_peak * np.array([0.99, 1, 1.01]))
    assert ps[1] == pytest.approx(spec.omega_p_h2(), rel=1e-12)
    assert ps[1] > ps[0]
    assert ps[1] > ps[2]


def test_asymmetric_break():
    r"""$f_p = f_b (-n_1/n_2)^{1/a_1}$, p. 6."""
    spec = spectrum(cls=AsymmetricBPL2024)
    assert spec.f_peak() == pytest.approx(spec.f_b() * 3**(1 / 2))
    ps, _ = spec.power_spectrum(np.array([spec.f_b()]))
    assert ps[0] == pytest.approx(spec.omega_b_h2())


@pytest.mark.parametrize("cls", [PowerSpectrumBPL2024, AsymmetricBPL2024])
def test_alternative_form(cls: type[PowerSpectrumBPL2024]):
    """The spectrum should equal the alternative form in terms of the peak, eq. 2.6."""
    spec = spectrum(cls=cls)
    (n1, n2), (a1,) = spec.SLOPES, spec.SMOOTHNESS
    f = spec.f_peak() * np.logspace(-3, 3, 13)
    x = f / spec.f_peak()
    alternative = spec.omega_p_h2() * (n1 - n2)**((n1 - n2) / a1) / (
        -n2 * x**(-n1 * a1 / (n1 - n2)) + n1 * x**(-n2 * a1 / (n1 - n2))
    )**((n1 - n2) / a1)
    np.testing.assert_allclose(spec.power_spectrum(f)[0], alternative, rtol=1e-10)


def test_slopes():
    """The spectrum should behave as f^2.4 and f^-2.4, table 1."""
    spec = spectrum()
    for f, slope in ((1e-5 * spec.f_peak(), 2.4), (1e5 * spec.f_peak(), -2.4)):
        ps = spec.shape(np.array([f, 1.001 * f]))
        assert np.log(ps[1] / ps[0]) / np.log(1.001) == pytest.approx(slope, abs=0.01)


def test_power_spectrum_reference():
    """Regression test against the output of the first implementation."""
    spec = spectrum()
    ps, _ = spec.power_spectrum(np.array([spec.f_peak() / 10]))
    np.testing.assert_allclose([spec.omega_p_h2(), spec.f_peak(), ps[0]], REFERENCE, rtol=1e-6)
