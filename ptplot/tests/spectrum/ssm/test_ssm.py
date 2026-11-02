"""Tests for the Sound Shell Model (SSM) power spectrum."""

import unittest

import numpy as np
from pttools.bubble import Bubble
from pttools.models import BagModel
from pttools.omgw0 import Spectrum, SuppressionMethod
from pttools.ssm.nucleation import DEFAULT_NUC_TYPE, NucType
from pttools.ssm.suppression import DEFAULT_SUPPRESSION
import pytest

from ptplot.science.const import OMEGA_PHOTON_H2
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

    def test_nuc_type(self) -> None:
        r"""The nucleation type should change the bubble lifetime distribution but not $r_*$.

        The reference is the PTtools spectrum with the $r_*$ of the SSM spectrum,
        which was used for the simultaneous nucleation by :py:func:`ptplot.science.plot.lattice.ssm_curves`
        before :py:meth:`PowerSpectrumSSM.power_spectrum` had the argument ``nuc_type``.
        As the spectra are given $\beta/H_*$, PTtools computes $r_*$ from it,
        including the thermal suppression of nucleation for the deflagration.
        """
        noise = noise_curve()
        assert DEFAULT_NUC_TYPE == NucType.EXPONENTIAL
        for v_wall in V_WALLS:
            ssm = spectrum(v_wall, settings=TEST_SSM_SETTINGS)
            ps_default, snr_default = ssm.power_spectrum(noise.f, noise=noise)
            for nuc_type in NucType:
                with self.subTest(v_wall=v_wall, nuc_type=nuc_type):
                    ps, snr = ssm.power_spectrum(noise.f, noise=noise, nuc_type=nuc_type)
                    assert ssm.spectrum is not None
                    assert ssm.spectrum.nuc_type == nuc_type
                    np.testing.assert_allclose(ssm.spectrum.r_star, ssm.r_star, rtol=1e-12)
                    ref = Spectrum(
                        bubble=ssm.bubble, f=noise.f, r_star=ssm.r_star, T_star=ssm.T_star, g_star=ssm.g_star,
                        nuc_type=nuc_type,
                        suppression=DEFAULT_SUPPRESSION, suppression_method=SuppressionMethod.EXT_CONSTANT,
                        **ssm.settings.spectrum_kwargs()
                    )
                    ps_ref = ref.omgw0_h2(om_gamma0_h2=OMEGA_PHOTON_H2)
                    np.testing.assert_allclose(ps, ps_ref, rtol=1e-12)
                    np.testing.assert_allclose(snr, ssm.snr(noise.f, ps_ref, noise), rtol=1e-12)
                    if nuc_type == DEFAULT_NUC_TYPE:
                        np.testing.assert_allclose(ps, ps_default, rtol=1e-12)
                        np.testing.assert_allclose(snr, snr_default, rtol=1e-12)
                    else:
                        assert not np.allclose(ps, ps_default, rtol=1e-2, atol=0)

    @staticmethod
    def test_bubble_mismatch() -> None:
        """A fluid shell that does not match the parameters of the spectrum should be rejected."""
        bubble = Bubble.cached(model=BAG, v_wall=0.3, alpha_n=ALPHA)
        with pytest.raises(ValueError, match="same v_wall and alpha"):
            spectrum(0.9, bubble=bubble)
        with pytest.raises(ValueError, match="same model"):
            spectrum(0.3, bubble=bubble, model=BagModel(alpha_n_min=0.0001))
