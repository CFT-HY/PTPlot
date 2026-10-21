"""Tests for the precomputed Sound Shell Model (SSM) power spectra."""

import typing as tp
import unittest

import numpy as np
from pttools.bubble import Bubble
from pttools.omgw0 import Spectrum, SuppressionMethod
import pytest

from ptplot.science.noise import noise_curve
from ptplot.science.spectrum.ssm import BAG, PowerSpectrumSSM
from ptplot.tests.const import TEST_SSM_SETTINGS
from ptplot.tests.spectrum.ssm.common import (
    ALPHA,
    BETA_TILDE,
    BETA_TILDES,
    G_STAR,
    T_STAR,
    V_WALLS,
    spectrum,
)


class SSMPrecomputedTest(unittest.TestCase):
    """Tests for precomputing the SSM power spectrum for a $z$ array and reusing it.

    The tests of the SSM are divided into several classes so that pytest-xdist can run them in parallel,
    as each class is run on a single worker.
    """

    @staticmethod
    def test_settings_covering() -> None:
        """Only n_z_lookup should be scaled for a z array that spans more decades than the frequencies."""
        noise = noise_curve()
        bubble = Bubble.cached(model=BAG, v_wall=V_WALLS[0], alpha_n=ALPHA)
        z = PowerSpectrumSSM.z_covering(
            f=noise.f, bubble=bubble, T_star=T_STAR, g_star=G_STAR, beta_tilde=np.array(BETA_TILDES))
        settings = PowerSpectrumSSM.settings_covering(z=z, f=noise.f, settings=TEST_SSM_SETTINGS)
        assert settings.n_z_lookup == PowerSpectrumSSM.n_z_lookup_covering(
            z=z, f=noise.f, n_z_lookup=TEST_SSM_SETTINGS.n_z_lookup)
        assert settings.n_z_lookup > TEST_SSM_SETTINGS.n_z_lookup
        assert settings.n_t == TEST_SSM_SETTINGS.n_t
        assert settings.nx_p_tilde_gw == TEST_SSM_SETTINGS.nx_p_tilde_gw

    @staticmethod
    def test_precomputed_fallback() -> None:
        """The spectrum should be computed for the frequencies if the precomputed spectrum cannot be used."""
        noise = noise_curve()
        bubble = Bubble.cached(model=BAG, v_wall=V_WALLS[0], alpha_n=ALPHA)
        z = PowerSpectrumSSM.z_covering(
            f=noise.f[:noise.f.size // 2], bubble=bubble, T_star=T_STAR, g_star=G_STAR,
            beta_tilde=np.array([BETA_TILDE]))
        ssm = spectrum(V_WALLS[0], bubble=bubble, z=z, settings=TEST_SSM_SETTINGS)
        computed = spectrum(V_WALLS[0], bubble=bubble, settings=TEST_SSM_SETTINGS)
        ps_ref, snr_ref = computed.power_spectrum(noise.f, noise=noise)

        # The frequencies are outside the precomputed range.
        assert not ssm.covers(noise.f)
        ps, snr = ssm.power_spectrum(noise.f, noise=noise)
        assert ssm.spectrum is not None
        assert ssm.precomputed is not None
        assert ssm.spectrum.a2 is not ssm.precomputed.a2
        np.testing.assert_allclose(ps, ps_ref, rtol=1e-12)
        np.testing.assert_allclose(snr, snr_ref, rtol=1e-12)

        # The suppression method differs from that of the precomputed spectrum.
        f = noise.f[:noise.f.size // 4]
        assert ssm.covers(f)
        ps, _ = ssm.power_spectrum(f, noise=noise, suppression_method=SuppressionMethod.NONE)
        assert ssm.spectrum is not None
        assert ssm.spectrum.a2 is not ssm.precomputed.a2
        ps_ref, _ = computed.power_spectrum(f, noise=noise, suppression_method=SuppressionMethod.NONE)
        np.testing.assert_allclose(ps, ps_ref, rtol=1e-12)

    def test_with_params(self) -> None:
        """A spectrum created with with_params() should match one created with the same parameters."""
        noise = noise_curve()
        bubble = Bubble.cached(model=BAG, v_wall=V_WALLS[0], alpha_n=ALPHA)
        z = PowerSpectrumSSM.z_covering(
            f=noise.f, bubble=bubble, T_star=T_STAR, g_star=G_STAR, beta_tilde=np.array(BETA_TILDES))
        cases: list[tuple[dict[str, tp.Any], dict[str, tp.Any]]] = [
            ({"beta_tilde": 1000.}, {"beta_tilde": 1000.}),
            ({"r_star": 0.01}, {"beta_tilde": None, "r_star": 0.01}),
            ({"T_star": 200., "g_star": 50.}, {"T_star": 200., "g_star": 50.}),
            ({"f_star0_factor": 1.1}, {"f_star0_factor": 1.1}),
        ]
        for z_i in (None, z):
            base = spectrum(V_WALLS[0], bubble=bubble, z=z_i, settings=TEST_SSM_SETTINGS)
            for params, kwargs in cases:
                with self.subTest(z=z_i is not None, **params):
                    new = base.with_params(**params)
                    ref = spectrum(V_WALLS[0], bubble=bubble, settings=TEST_SSM_SETTINGS, **kwargs)
                    assert new.bubble is bubble
                    assert (new.precomputed is None) == (z_i is None)
                    np.testing.assert_allclose(new.r_star, ref.r_star, rtol=1e-12)
                    np.testing.assert_allclose(new.beta_tilde, ref.beta_tilde, rtol=1e-12)
                    np.testing.assert_allclose(new.H_star_eta_sh, ref.H_star_eta_sh, rtol=1e-12)
                    if z_i is not None:
                        ref = spectrum(V_WALLS[0], bubble=bubble, z=z_i, settings=TEST_SSM_SETTINGS, **kwargs)
                        assert new.precomputed is not None
                        assert ref.precomputed is not None
                        np.testing.assert_array_equal(new.precomputed.y, z_i)
                        np.testing.assert_allclose(
                            new.precomputed.omgw0_h2(), ref.precomputed.omgw0_h2(), rtol=1e-12)
                    f = noise.f[noise.f.size // 4:]
                    ps, snr = new.power_spectrum(f, noise=noise)
                    ps_ref, snr_ref = ref.power_spectrum(f, noise=noise)
                    np.testing.assert_allclose(ps, ps_ref, rtol=1e-12)
                    np.testing.assert_allclose(snr, snr_ref, rtol=1e-12)

        # The parameters given as alpha or ubarf should be preserved.
        ubarf = base.ubarf
        given_ubarf = spectrum(V_WALLS[0], alpha=None, ubarf=ubarf)
        assert given_ubarf.with_params(beta_tilde=1000.).ubarf == ubarf

    @staticmethod
    def test_z_covering() -> None:
        """The z array should cover the frequencies for all the given values, ignoring the invalid ones."""
        noise = noise_curve()
        bubble = Bubble.cached(model=BAG, v_wall=V_WALLS[0], alpha_n=ALPHA)
        for name, values in (("beta_tilde", BETA_TILDES), ("r_star", (1e-3, 0.01, 0.1))):
            # The invalid values should be ignored.
            arr = np.array([*values, np.nan, -1.])
            z = PowerSpectrumSSM.z_covering(
                f=noise.f, bubble=bubble, T_star=T_STAR, g_star=G_STAR, f_star0_factor=1.1,
                beta_tilde=arr if name == "beta_tilde" else None,
                r_star=arr if name == "r_star" else None
            )
            assert np.all(np.diff(z) > 0)
            # The default density is that of the frequencies.
            points_per_decade = (z.size - 1) / np.log10(z[-1] / z[0])
            np.testing.assert_allclose(
                points_per_decade, (noise.f.size - 1) / np.log10(noise.f[-1] / noise.f[0]), rtol=1e-3)
            spectra = [
                spectrum(
                    V_WALLS[0], bubble=bubble, z=z, f_star0_factor=1.1, settings=TEST_SSM_SETTINGS,
                    beta_tilde=value if name == "beta_tilde" else None,
                    r_star=value if name == "r_star" else None
                )
                for value in values
            ]
            for ssm in spectra:
                assert ssm.covers(noise.f)
            # The smallest and largest r_star determine the endpoints.
            spectra.sort(key=lambda ssm: tp.cast(Spectrum, ssm.precomputed).r_star)
            assert not spectra[0].covers(noise.f / 1.01)
            assert not spectra[-1].covers(noise.f * 1.01)
        with pytest.raises(ValueError, match="Exactly one"):
            PowerSpectrumSSM.z_covering(f=noise.f, bubble=bubble, T_star=T_STAR, g_star=G_STAR)
        with pytest.raises(ValueError, match="None of"):
            PowerSpectrumSSM.z_covering(
                f=noise.f, bubble=bubble, T_star=T_STAR, g_star=G_STAR, beta_tilde=np.array([np.nan]))
