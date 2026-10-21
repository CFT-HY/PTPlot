"""Tests that compare the precomputed SSM spectra and SNR grid columns to separately computed spectra."""

from pathlib import Path
import tempfile
import unittest

import numpy as np
from pttools.bubble import Bubble
from pttools.export import Exporter, Extractor, Importer, Preset, Table
from pttools.omgw0 import Spectrum
from pttools.ssm.const import DEFAULT_N_Z_LOOKUP

from ptplot.science.noise import noise_curve
from ptplot.science.snr.ssm import snr_column_ssm
from ptplot.science.spectrum.ssm import BAG, PowerSpectrumSSM
from ptplot.tests.spectrum.ssm.common import (
    ALPHA,
    BETA_TILDE,
    BETA_TILDES,
    G_STAR,
    PS_REL_MIN_PRECOMPUTED,
    PS_RTOL_PRECOMPUTED,
    SNR_RTOL_PRECOMPUTED,
    T_STAR,
    V_WALLS,
    reference,
    spectrum,
)


class SSMReferenceTest(unittest.TestCase):
    """Tests that compare the precomputed SSM spectra and the SNR grid columns to separately computed spectra.

    These are in the same class, as they share the spectra cached by
    :py:func:`ptplot.tests.spectrum.ssm.common.reference`.
    """

    def test_precomputed(self) -> None:
        r"""A precomputed spectrum should give the same results as computing the spectrum for the frequencies.

        The SNR is computed on different points, and the power spectrum is interpolated.
        The lookup arrays are as dense as for the frequencies, see :py:meth:`PowerSpectrumSSM.n_z_lookup_covering`.
        Even then, the power spectrum of PTtools depends on the range of the $z$ array,
        as the lookup array of $qT$ for ${\lvert A \rvert}^2$ begins from the smallest $z$
        and has the same spacing as the $z$ array.
        With the spacing of the default noise curve, this discretization error is up to 2 % near the peak,
        and the same as the difference of a spectrum computed separately for the frequencies
        and one computed for a 4 times denser $z$ array.
        In the tail of the spectrum, the error is larger, and the tail does not converge with ``n_z_lookup``.
        Therefore, the power spectrum is compared only near the peak.
        """
        noise = noise_curve()
        beta_tildes = np.array(BETA_TILDES)
        for v_wall in V_WALLS:
            bubble = Bubble.cached(model=BAG, v_wall=v_wall, alpha_n=ALPHA)
            z = PowerSpectrumSSM.z_covering(
                f=noise.f, bubble=bubble, T_star=T_STAR, g_star=G_STAR, beta_tilde=beta_tildes)
            settings = PowerSpectrumSSM.settings_covering(z=z, f=noise.f)
            assert settings.n_z_lookup > DEFAULT_N_Z_LOOKUP
            # The spectra of the other beta_tilde values are created from the first one with with_params(),
            # which reuses its precomputed spectrum, as in snr_column_ssm().
            # It gives the same results as precomputing them separately, see SSMPrecomputedTest.test_with_params().
            shared = spectrum(v_wall, bubble=bubble, beta_tilde=BETA_TILDES[0], z=z, settings=settings)
            for beta_tilde in BETA_TILDES:
                with self.subTest(v_wall=v_wall, beta_tilde=beta_tilde):
                    precomputed = shared.with_params(beta_tilde=beta_tilde)
                    assert precomputed.precomputed is not None
                    assert precomputed.covers(noise.f)
                    ps, snr = precomputed.power_spectrum(noise.f, noise=noise)
                    # The stored spectrum is interpolated from the precomputed spectrum for exporting.
                    interpolated = precomputed.spectrum
                    assert interpolated is not None
                    assert interpolated.f_given
                    assert interpolated.a2 is precomputed.precomputed.a2
                    np.testing.assert_array_equal(interpolated.f(), noise.f)
                    np.testing.assert_array_equal(interpolated.omgw0_h2(), ps)
                    _, ps_ref, snr_ref = reference(v_wall, beta_tilde)
                    np.testing.assert_allclose(snr, snr_ref, rtol=SNR_RTOL_PRECOMPUTED)
                    significant = ps_ref > PS_REL_MIN_PRECOMPUTED * ps_ref.max()
                    np.testing.assert_allclose(ps[significant], ps_ref[significant], rtol=PS_RTOL_PRECOMPUTED)

    def test_snr_column(self) -> None:
        """The SNR grid column should match the individual spectra with the same parameters."""
        noise = noise_curve()
        for v_wall in V_WALLS:
            with self.subTest(v_wall=v_wall):
                ssm, _, snr = reference(v_wall)
                column = snr_column_ssm(
                    x=ALPHA, y=np.array([BETA_TILDE]), v_wall=v_wall, T_star=T_STAR, g_star=G_STAR, noise=noise
                )
                np.testing.assert_allclose(column.snr[0], snr, rtol=1e-6)
                np.testing.assert_allclose(column.shock_times[0], ssm.H_star_eta_sh, rtol=1e-12)
                assert not column.records

    def test_snr_column_multiple(self) -> None:
        """The SNR grid column with a shared spectrum should match the separately computed spectra."""
        noise = noise_curve()
        for v_wall in V_WALLS:
            with self.subTest(v_wall=v_wall):
                column = snr_column_ssm(
                    x=ALPHA, y=np.array(BETA_TILDES), v_wall=v_wall, T_star=T_STAR, g_star=G_STAR, noise=noise
                )
                for i, beta_tilde in enumerate(BETA_TILDES):
                    ssm, _, snr = reference(v_wall, beta_tilde)
                    np.testing.assert_allclose(column.snr[i], snr, rtol=SNR_RTOL_PRECOMPUTED)
                    np.testing.assert_allclose(column.shock_times[i], ssm.H_star_eta_sh, rtol=1e-12)

    def test_export_column(self) -> None:
        """The exported spectra of an SNR grid column should match the spectra computed by PTPlot.

        The spectra are interpolated from the shared spectrum of the column,
        and exported with the frequencies of the noise curve as the grid.
        They should share the fluid shell and the model of the column.
        The SNR of PTtools with only the instrument noise is computed on the frequencies of the noise curve,
        and should match that of PTPlot with its default noise curve,
        which is computed on the points of the shared spectrum.
        The spectra should be recreatable from the file.
        As they are then computed for the frequencies, they match the exported spectra
        within the accuracy of the shared spectrum, see :py:meth:`test_precomputed`.
        """
        noise = noise_curve()
        v_wall = V_WALLS[0]
        y = np.array([BETA_TILDE, BETA_TILDES[2]])
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "spectra.h5"
            with Exporter(path, spectrum_fields=(Preset.MINIMAL, Preset.FULL)) as exporter:
                column = snr_column_ssm(
                    x=ALPHA, y=y, v_wall=v_wall, T_star=T_STAR, g_star=G_STAR, noise=noise,
                    extractor=exporter.extractor
                )
                exporter.add_many(column.records)
            with Importer(path, verify=True) as importer:
                assert importer.n_spectra_f == y.size
                assert importer.n_spectra_y == 0
                assert importer.n_bubbles == 1
                assert importer.n_models == 1
                np.testing.assert_array_equal(importer.read(Table.SPECTRA_F, "f"), noise.f)
                np.testing.assert_allclose(importer.read(Table.SPECTRA_F, "beta_tilde"), y, rtol=1e-15)
                np.testing.assert_allclose(
                    importer.read(Table.SPECTRA_F, "snr_ins"), column.snr, rtol=SNR_RTOL_PRECOMPUTED)
                omgw0_h2 = importer.read(Table.SPECTRA_F, "omgw0_h2")
                loaded = importer.load_spectrum(0, table=Table.SPECTRA_F, parallel=False)
        assert isinstance(loaded, Spectrum)
        significant = omgw0_h2[0] > PS_REL_MIN_PRECOMPUTED * omgw0_h2[0].max()
        np.testing.assert_allclose(
            loaded.omgw0_h2()[significant], omgw0_h2[0][significant], rtol=PS_RTOL_PRECOMPUTED)

        bubble = Bubble.cached(model=BAG, v_wall=v_wall, alpha_n=ALPHA)
        z = PowerSpectrumSSM.z_covering(f=noise.f, bubble=bubble, T_star=T_STAR, g_star=G_STAR, beta_tilde=y)
        shared = spectrum(
            v_wall, bubble=bubble, beta_tilde=y[0], z=z, settings=PowerSpectrumSSM.settings_covering(z=z, f=noise.f))
        for i, beta_tilde in enumerate(y):
            ps_shared, _ = shared.with_params(beta_tilde=beta_tilde).power_spectrum(noise.f, noise=noise)
            np.testing.assert_allclose(omgw0_h2[i], ps_shared, rtol=1e-12)
            _, ps_ref, _ = reference(v_wall, beta_tilde)
            significant = ps_ref > PS_REL_MIN_PRECOMPUTED * ps_ref.max()
            np.testing.assert_allclose(omgw0_h2[i][significant], ps_ref[significant], rtol=PS_RTOL_PRECOMPUTED)

    @staticmethod
    def test_snr_column_failures() -> None:
        """The failed points of a column should be NaN and not exported, and the other points should be computed."""
        noise = noise_curve()
        column = snr_column_ssm(
            x=ALPHA, y=np.array([BETA_TILDE, np.nan]), v_wall=V_WALLS[0], T_star=T_STAR, g_star=G_STAR, noise=noise,
            extractor=Extractor()
        )
        assert np.isfinite(column.snr[0])
        assert np.isfinite(column.shock_times[0])
        assert np.isnan(column.snr[1])
        assert np.isnan(column.shock_times[1])
        assert len(column.records) == 1

        # The fluid shell cannot be created, as alpha_n is below the minimum of the model.
        column = snr_column_ssm(
            x=BAG.alpha_n_min / 10, y=np.array([BETA_TILDE]), v_wall=V_WALLS[0], T_star=T_STAR, g_star=G_STAR,
            noise=noise, extractor=Extractor()
        )
        assert np.all(np.isnan(column.snr))
        assert np.all(np.isnan(column.shock_times))
        assert not column.records
