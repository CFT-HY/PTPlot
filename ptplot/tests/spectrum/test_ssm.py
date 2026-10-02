"""Sound Shell Model (SSM) tests."""

import typing as tp
import unittest

import numpy as np
from pttools.bubble import Bubble
from pttools.models import BagModel
import pytest

from ptplot.science.noise import noise_curve
from ptplot.science.snr.ssm import snr_column_ssm
from ptplot.science.spectrum.ssm import BAG, PowerSpectrumSSM
from ptplot.tests.spectrum.base import PowerSpectrumBaseCase

ALPHA: float = 0.1
BETA_TILDE: float = 100.
T_STAR: float = 100.
G_STAR: float = 100.
#: Subsonic deflagration and detonation
V_WALLS: tuple[float, ...] = (0.3, 0.9)
#: Reference values of $r_*$, SNR and $\mathcal{H}_* \eta_\text{sh}$ for each wall velocity,
#: computed with PTPlot before the fix of the ``bubble`` argument of :class:`PowerSpectrumSSM` in October 2026
REFERENCE: dict[float, tuple[float, float, float]] = {
    0.3: (0.018124666532740186, 0.05726717628625229, 0.19839872059716177),
    0.9: (0.026362653976107417, 0.11508301979789859, 0.2568295035856295),
}


def spectrum(v_wall: float, **kwargs: tp.Any) -> PowerSpectrumSSM:
    """Create an SSM power spectrum with the test parameters."""
    return PowerSpectrumSSM(
        v_wall=v_wall, alpha=ALPHA, beta_tilde=BETA_TILDE, T_star=T_STAR, g_star=G_STAR, **kwargs
    )


class SSMTest(PowerSpectrumBaseCase[PowerSpectrumSSM], unittest.TestCase):
    """Tests for the Sound Shell Model (SSM) power spectrum."""

    SPECTRUM_CLASS = PowerSpectrumSSM

    def test_reference(self) -> None:
        r"""$r_*$, the SNR and $\mathcal{H}_* \eta_\text{sh}$ should match the reference values."""
        noise = noise_curve()
        for v_wall, (r_star, snr, shock_time) in REFERENCE.items():
            with self.subTest(v_wall=v_wall):
                ssm = spectrum(v_wall)
                _, snr_new = ssm.power_spectrum(noise.f, noise=noise)
                np.testing.assert_allclose(ssm.r_star, r_star, rtol=1e-12)
                np.testing.assert_allclose(snr_new, snr, rtol=1e-6)
                np.testing.assert_allclose(ssm.H_star_eta_sh, shock_time, rtol=1e-12)

    def test_bubble(self) -> None:
        """A precomputed fluid shell should be used and give the same results as computing it."""
        noise = noise_curve()
        for v_wall in V_WALLS:
            with self.subTest(v_wall=v_wall):
                bubble = Bubble(model=BAG, v_wall=v_wall, alpha_n=ALPHA)
                given = spectrum(v_wall, bubble=bubble)
                computed = spectrum(v_wall)
                assert given.bubble is bubble
                assert given.model is BAG
                assert given.nu_gdh2024 == computed.nu_gdh2024
                np.testing.assert_allclose(given.r_star, computed.r_star, rtol=1e-12)
                np.testing.assert_allclose(given.H_star_eta_sh, computed.H_star_eta_sh, rtol=1e-12)
                ps_given, snr_given = given.power_spectrum(noise.f, noise=noise)
                ps_computed, snr_computed = computed.power_spectrum(noise.f, noise=noise)
                np.testing.assert_allclose(ps_given, ps_computed, rtol=1e-6)
                np.testing.assert_allclose(snr_given, snr_computed, rtol=1e-6)

    @staticmethod
    def test_bubble_mismatch() -> None:
        """A fluid shell that does not match the parameters of the spectrum should be rejected."""
        bubble = Bubble(model=BAG, v_wall=0.3, alpha_n=ALPHA)
        with pytest.raises(ValueError, match="same v_wall and alpha"):
            spectrum(0.9, bubble=bubble)
        with pytest.raises(ValueError, match="same model"):
            spectrum(0.3, bubble=bubble, model=BagModel(alpha_n_min=0.0001))

    def test_snr_column(self) -> None:
        """The SNR grid column should match the individual spectra with the same parameters."""
        noise = noise_curve()
        for v_wall in V_WALLS:
            with self.subTest(v_wall=v_wall):
                ssm = spectrum(v_wall)
                _, snr = ssm.power_spectrum(noise.f, noise=noise)
                column = snr_column_ssm(
                    x=ALPHA, y=np.array([BETA_TILDE]), v_wall=v_wall, T_star=T_STAR, g_star=G_STAR, noise=noise
                )
                np.testing.assert_allclose(column[0, 0], snr, rtol=1e-6)
                np.testing.assert_allclose(column[1, 0], ssm.H_star_eta_sh, rtol=1e-12)
