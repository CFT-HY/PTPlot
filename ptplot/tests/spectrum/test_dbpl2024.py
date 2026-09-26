r"""Double broken power law (DBPL) tests (2024 version).

The equation and page numbers refer to :caprini_2024:`\ ` arXiv:2403.03723v2.
"""

import unittest

import numpy as np
import pytest
from scipy.integrate import quad

from ptplot.science import const
from ptplot.science.spectrum.dbpl2024 import PowerSpectrumDBPL2024
from ptplot.tests.spectrum.base_spectrum import PowerSpectrumBaseCase

#: Reference values of $h^2 \Omega_{\text{int}}$, $h^2 \Omega_2$ and $h^2 \Omega_{\text{gw}}(f_1)$
#: for the default parameters of :func:`spectrum`, from the first implementation
REFERENCE = np.array([1.2910820190499549e-11, 6.966806570012265e-12, 1.0191520402793716e-12])


class DBPL2024Test(PowerSpectrumBaseCase, unittest.TestCase):
    """Tests for the double broken power law (DBPL) power spectrum of 2024."""

    SPECTRUM_CLASS = PowerSpectrumDBPL2024


def spectrum(v_wall: float = 0.9, alpha: float = 0.1, r_star: float = 0.1) -> PowerSpectrumDBPL2024:
    """Create a DBPL2024 spectrum with $T_* = 100$ GeV and $g_* = 100$."""
    return PowerSpectrumDBPL2024(T_star=100, g_star=100, v_wall=v_wall, alpha=alpha, r_star=r_star)


def test_break_frequencies():
    """The break frequencies should follow eq. 2.2 and 2.9."""
    spec = spectrum(v_wall=0.9, r_star=0.1)
    delta_w = (0.9 - const.CS0) / 0.9
    assert spec.f1() == pytest.approx(0.2 * 1.65e-5 / 0.1)
    assert spec.f2() == pytest.approx(0.5 * 1.65e-5 / (delta_w * 0.1))


def test_break_ratio_detonation():
    r"""$f_2/f_1 \approx 5.9$ and $\Omega_2 \approx 0.55 \Omega_{\text{int}}$ for $\xi_w \approx 1$, p. 11 and 18."""
    spec = spectrum(v_wall=0.999)
    assert spec.f2() / spec.f1() == pytest.approx(5.9, abs=0.05)
    assert spec.omega_2_h2() / spec.omega_int_h2() == pytest.approx(0.55, abs=0.01)


def test_delta_w_deflagration():
    r"""$\Delta_w = \xi_{\text{shell}} / \max(\xi_w, c_s)$ should use $c_s$ for subsonic walls."""
    assert spectrum(v_wall=0.4).delta_w == pytest.approx((const.CS0 - 0.4) / const.CS0)


@pytest.mark.parametrize("v_wall", [0.4, 0.7, 0.9, 0.999])
def test_omega_2_normalization(v_wall: float):
    r"""Eq. 2.12 should equal $\Omega_{\text{int}} / \int d \ln f S_2(f)$, as $\int d \ln f S(f) = 1$."""
    spec = spectrum(v_wall=v_wall)
    integral = quad(lambda ln_f: spec.shape(np.exp(ln_f)), -30, 0, limit=500)[0]
    assert spec.omega_2_h2() * integral == pytest.approx(spec.omega_int_h2(), rel=1e-8)


def test_S2_normalization():
    r"""$S_2(f_2) = 1$."""
    spec = spectrum()
    assert spec.shape(spec.f2()) == pytest.approx(1)


def test_slopes():
    """The spectrum should behave as f^3, f^1 and f^-3, eq. 2.8 and table 1."""
    spec = spectrum(v_wall=0.999, r_star=1e-3)
    f1 = spec.f1()
    f2 = spec.f2()
    for f, slope in ((1e-4 * f1, 3), (np.sqrt(f1 * f2), 1), (1e4 * f2, -3)):
        ps = spec.shape(np.array([f, 1.001 * f]))
        assert np.log(ps[1] / ps[0]) / np.log(1.001) == pytest.approx(slope, abs=0.2)


def test_f_peak():
    """The peak frequency should be a local maximum of the spectrum."""
    spec = spectrum()
    f_peak = spec.f_peak()
    assert spec.d_ln_S_d_ln_f(np.log(f_peak)) == pytest.approx(0, abs=1e-9)
    ps = spec.shape(f_peak * np.array([0.99, 1, 1.01]))
    assert ps[1] > ps[0]
    assert ps[1] > ps[2]


@pytest.mark.parametrize("r_star", [1e-3, 0.5])
def test_omega_int(r_star: float):
    r"""Eq. 2.10 with $K = 0.6 \Gamma \bar{U}_f^2$ and $\mathcal{H}_* \eta_{\text{sw}} = \min(r_* / \bar{v}_f, 1)$."""
    spec = spectrum(r_star=r_star)
    kinetic_energy_fraction = 0.6 * spec.adiabatic_index * spec.ubarf**2
    h_star_eta_sw = min(r_star / np.sqrt(kinetic_energy_fraction / spec.adiabatic_index), 1)
    assert spec.kinetic_energy_fraction == pytest.approx(kinetic_energy_fraction)
    assert spec.H_star_eta_sw == pytest.approx(h_star_eta_sw)
    assert spec.omega_int_h2() == pytest.approx(
        spec.F_gw0_h2() * 0.11 * kinetic_energy_fraction**2 * h_star_eta_sw * r_star, rel=1e-12
    )


def test_source_duration_cap():
    """A long-lasting source should be capped at the Hubble time."""
    assert spectrum(r_star=0.5).H_star_eta_sw == 1


def test_F_gw0_h2():
    """The redshift factor should agree with eq. 2.3 to 1 %."""
    assert spectrum().F_gw0_h2() == pytest.approx(1.64e-5, rel=0.01)


def test_power_spectrum_reference():
    """Regression test against the output of the first implementation."""
    spec = spectrum()
    ps, _ = spec.power_spectrum(np.array([spec.f1(), spec.f2()]))
    assert ps[1] == pytest.approx(spec.omega_2_h2(), rel=1e-12)
    np.testing.assert_allclose([spec.omega_int_h2(), spec.omega_2_h2(), ps[0]], REFERENCE, rtol=1e-6)


def test_v_wall_cs():
    """A zero sound shell thickness should be rejected."""
    with pytest.raises(ValueError, match="sound shell thickness"):
        spectrum(v_wall=const.CS0)
