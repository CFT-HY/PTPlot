"""Tests for the Sound Shell Model (SSM) power spectrum."""

import unittest

import numpy as np
from pttools.bubble import Bubble
from pttools.models import BagModel
import pytest

from ptplot.science.noise import noise_curve
from ptplot.science.spectrum.ssm import BAG, PowerSpectrumSSM
from ptplot.tests.const import TEST_SSM_SETTINGS
from ptplot.tests.spectrum.base import PowerSpectrumBaseCase
from ptplot.tests.spectrum.ssm.common import (
    ALPHA,
    F_STAR0_FACTOR,
    REFERENCE,
    V_WALLS,
    spectrum,
)


class SSMTest(PowerSpectrumBaseCase[PowerSpectrumSSM], unittest.TestCase):
    """Tests for the Sound Shell Model (SSM) power spectrum."""

    SPECTRUM_CLASS = PowerSpectrumSSM
    # The default noise curve of PTPlot has only the instrument noise.
    SNR_FIELD = "snr_ins"

    def test_reference(self) -> None:
        r"""$r_*$, the SNR and $\mathcal{H}_* \eta_\text{sh}$ should match the reference values."""
        noise = noise_curve(eb=True, gb=True)
        for v_wall, (r_star, snr, shock_time) in REFERENCE.items():
            with self.subTest(v_wall=v_wall):
                ssm = spectrum(v_wall, f_star0_factor=F_STAR0_FACTOR)
                _, snr_new = ssm.power_spectrum(noise.f, noise=noise)
                np.testing.assert_allclose(ssm.r_star, r_star, rtol=1e-12)
                np.testing.assert_allclose(snr_new, snr, rtol=1e-6)
                np.testing.assert_allclose(ssm.H_star_eta_sh, shock_time, rtol=1e-12)

    @staticmethod
    def test_f_star0_factor() -> None:
        r"""Scaling $f_{\ast,0}$ and $f$ by the same factor should give the same $\Omega_{\text{gw},0} h^2$."""
        noise = noise_curve()
        factor = 1.5
        ps, _ = spectrum(V_WALLS[0], settings=TEST_SSM_SETTINGS).power_spectrum(noise.f, noise=noise)
        ps_scaled, _ = spectrum(V_WALLS[0], f_star0_factor=factor, settings=TEST_SSM_SETTINGS) \
            .power_spectrum(factor * noise.f, noise=noise)
        np.testing.assert_allclose(ps_scaled, ps, rtol=1e-12)

    def test_bubble(self) -> None:
        """A precomputed fluid shell should be used and give the same results as computing it."""
        noise = noise_curve()
        for v_wall in V_WALLS:
            with self.subTest(v_wall=v_wall):
                bubble = Bubble.cached(model=BAG, v_wall=v_wall, alpha_n=ALPHA)
                given = spectrum(v_wall, bubble=bubble, settings=TEST_SSM_SETTINGS)
                computed = spectrum(v_wall, settings=TEST_SSM_SETTINGS)
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
        bubble = Bubble.cached(model=BAG, v_wall=0.3, alpha_n=ALPHA)
        with pytest.raises(ValueError, match="same v_wall and alpha"):
            spectrum(0.9, bubble=bubble)
        with pytest.raises(ValueError, match="same model"):
            spectrum(0.3, bubble=bubble, model=BagModel(alpha_n_min=0.0001))
