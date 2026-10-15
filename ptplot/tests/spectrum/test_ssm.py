"""Sound Shell Model (SSM) tests."""

from pathlib import Path
import tempfile
import typing as tp
import unittest

import numpy as np
from pttools.bubble import Bubble
from pttools.export import Exporter, Extractor, Importer, Preset, Table
from pttools.models import BagModel
from pttools.omgw0 import Spectrum, SuppressionMethod
from pttools.ssm.const import DEFAULT_N_Z_LOOKUP
import pytest

from ptplot.science.noise import noise_curve
from ptplot.science.snr.ssm import snr_column_ssm
from ptplot.science.spectrum.ssm import BAG, PowerSpectrumSSM
from ptplot.tests.old_ptplot import f_star0_factor
from ptplot.tests.spectrum.base import PowerSpectrumBaseCase

ALPHA: float = 0.1
BETA_TILDE: float = 100.
T_STAR: float = 100.
G_STAR: float = 100.
#: Subsonic deflagration and detonation
V_WALLS: tuple[float, ...] = (0.3, 0.9)
#: Reference values of $r_*$, SNR and $\mathcal{H}_* \eta_\text{sh}$ for each wall velocity,
#: computed with PTPlot before the fix of the ``bubble`` argument of :class:`PowerSpectrumSSM` in October 2026,
#: and therefore with the old $f_{\ast,0}$ of PTtools, see :py:data:`F_STAR0_FACTOR`,
#: and with the compact binary noises, which were included by default at the time.
#: The SNR values have since been updated for the following changes in PTtools:
#:
#: - 3d5798f: the point at the wall of detonations is in the broken phase (v_wall = 0.9: 0.11508 -> 0.11346)
#: - 137b476: the suppression datasets are recomputed with SSMSpectrum
#:   (v_wall = 0.3: 0.05727 -> 0.06623, v_wall = 0.9: 0.11346 -> 0.10879)
REFERENCE: dict[float, tuple[float, float, float]] = {
    0.3: (0.018124666532740186, 0.06622525560700972, 0.19839872059716177),
    0.9: (0.026362653976107417, 0.10878839586399065, 0.2568295035856295),
}

#: $\tilde{\beta}$ values of the columns for testing the precomputed spectra, covering 4 orders of magnitude
BETA_TILDES: tuple[float, ...] = (10., 100., 1000., 1e5)
#: Relative tolerance for the SNR computed on the points of a precomputed spectrum.
#: The SNR differs from that of a separately computed spectrum due to the different points.
SNR_RTOL_PRECOMPUTED: float = 1e-3
#: Relative tolerance for the power spectrum interpolated from a precomputed spectrum
#: at the frequencies where it is above :py:data:`PS_REL_MIN_PRECOMPUTED` times its peak,
#: see :py:meth:`SSMTest.test_precomputed`.
PS_RTOL_PRECOMPUTED: float = 2e-2
PS_REL_MIN_PRECOMPUTED: float = 1e-2

#: Ratio of the old and the new $f_{\ast,0}$ of PTtools, see :py:func:`ptplot.tests.old_ptplot.f_star0_factor`
F_STAR0_FACTOR: float = f_star0_factor(T_STAR, G_STAR)


def spectrum(
        v_wall: float,
        alpha: float | None = ALPHA,
        beta_tilde: float | None = BETA_TILDE,
        T_star: float = T_STAR,
        g_star: float = G_STAR,
        **kwargs: tp.Any) -> PowerSpectrumSSM:
    """Create an SSM power spectrum with the test parameters, which can be overridden."""
    return PowerSpectrumSSM(
        v_wall=v_wall, alpha=alpha, beta_tilde=beta_tilde, T_star=T_star, g_star=g_star, **kwargs
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
        ps, _ = spectrum(V_WALLS[0]).power_spectrum(noise.f, noise=noise)
        ps_scaled, _ = spectrum(V_WALLS[0], f_star0_factor=factor).power_spectrum(factor * noise.f, noise=noise)
        np.testing.assert_allclose(ps_scaled, ps, rtol=1e-12)

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
            bubble = Bubble(model=BAG, v_wall=v_wall, alpha_n=ALPHA)
            z = PowerSpectrumSSM.z_covering(
                f=noise.f, bubble=bubble, T_star=T_STAR, g_star=G_STAR, beta_tilde=beta_tildes)
            n_z_lookup = PowerSpectrumSSM.n_z_lookup_covering(z=z, f=noise.f)
            assert n_z_lookup > DEFAULT_N_Z_LOOKUP
            for beta_tilde in BETA_TILDES:
                with self.subTest(v_wall=v_wall, beta_tilde=beta_tilde):
                    precomputed = spectrum(v_wall, bubble=bubble, beta_tilde=beta_tilde, z=z, n_z_lookup=n_z_lookup)
                    assert precomputed.precomputed is not None
                    assert precomputed.covers(noise.f)
                    ps, snr = precomputed.power_spectrum(noise.f, noise=noise)
                    assert precomputed.spectrum is precomputed.precomputed
                    computed = spectrum(v_wall, bubble=bubble, beta_tilde=beta_tilde)
                    ps_ref, snr_ref = computed.power_spectrum(noise.f, noise=noise)
                    np.testing.assert_allclose(snr, snr_ref, rtol=SNR_RTOL_PRECOMPUTED)
                    significant = ps_ref > PS_REL_MIN_PRECOMPUTED * ps_ref.max()
                    np.testing.assert_allclose(ps[significant], ps_ref[significant], rtol=PS_RTOL_PRECOMPUTED)

    @staticmethod
    def test_precomputed_fallback() -> None:
        """The spectrum should be computed for the frequencies if the precomputed spectrum cannot be used."""
        noise = noise_curve()
        bubble = Bubble(model=BAG, v_wall=V_WALLS[0], alpha_n=ALPHA)
        z = PowerSpectrumSSM.z_covering(
            f=noise.f[:noise.f.size // 2], bubble=bubble, T_star=T_STAR, g_star=G_STAR,
            beta_tilde=np.array([BETA_TILDE]))
        ssm = spectrum(V_WALLS[0], bubble=bubble, z=z)
        computed = spectrum(V_WALLS[0], bubble=bubble)
        ps_ref, snr_ref = computed.power_spectrum(noise.f, noise=noise)

        # The frequencies are outside the precomputed range.
        assert not ssm.covers(noise.f)
        ps, snr = ssm.power_spectrum(noise.f, noise=noise)
        assert ssm.spectrum is not None
        assert ssm.spectrum is not ssm.precomputed
        np.testing.assert_allclose(ps, ps_ref, rtol=1e-12)
        np.testing.assert_allclose(snr, snr_ref, rtol=1e-12)

        # The suppression method differs from that of the precomputed spectrum.
        f = noise.f[:noise.f.size // 4]
        assert ssm.covers(f)
        ps, _ = ssm.power_spectrum(f, noise=noise, suppression_method=SuppressionMethod.NONE)
        assert ssm.spectrum is not ssm.precomputed
        ps_ref, _ = computed.power_spectrum(f, noise=noise, suppression_method=SuppressionMethod.NONE)
        np.testing.assert_allclose(ps, ps_ref, rtol=1e-12)

    def test_with_params(self) -> None:
        """A spectrum created with with_params() should match one created with the same parameters."""
        noise = noise_curve()
        bubble = Bubble(model=BAG, v_wall=V_WALLS[0], alpha_n=ALPHA)
        z = PowerSpectrumSSM.z_covering(
            f=noise.f, bubble=bubble, T_star=T_STAR, g_star=G_STAR, beta_tilde=np.array(BETA_TILDES))
        cases: list[tuple[dict[str, tp.Any], dict[str, tp.Any]]] = [
            ({"beta_tilde": 1000.}, {"beta_tilde": 1000.}),
            ({"r_star": 0.01}, {"beta_tilde": None, "r_star": 0.01}),
            ({"T_star": 200., "g_star": 50.}, {"T_star": 200., "g_star": 50.}),
            ({"f_star0_factor": 1.1}, {"f_star0_factor": 1.1}),
        ]
        for z_i in (None, z):
            base = spectrum(V_WALLS[0], bubble=bubble, z=z_i)
            for params, kwargs in cases:
                with self.subTest(z=z_i is not None, **params):
                    new = base.with_params(**params)
                    ref = spectrum(V_WALLS[0], bubble=bubble, **kwargs)
                    assert new.bubble is bubble
                    assert (new.precomputed is None) == (z_i is None)
                    np.testing.assert_allclose(new.r_star, ref.r_star, rtol=1e-12)
                    np.testing.assert_allclose(new.beta_tilde, ref.beta_tilde, rtol=1e-12)
                    np.testing.assert_allclose(new.H_star_eta_sh, ref.H_star_eta_sh, rtol=1e-12)
                    if z_i is not None:
                        ref = spectrum(V_WALLS[0], bubble=bubble, z=z_i, **kwargs)
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
        ubarf = spectrum(V_WALLS[0], bubble=bubble).ubarf
        given_ubarf = spectrum(V_WALLS[0], alpha=None, ubarf=ubarf)
        assert given_ubarf.with_params(beta_tilde=1000.).ubarf == ubarf

    @staticmethod
    def test_z_covering() -> None:
        """The z array should cover the frequencies for all the given values, ignoring the invalid ones."""
        noise = noise_curve()
        bubble = Bubble(model=BAG, v_wall=V_WALLS[0], alpha_n=ALPHA)
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
                    V_WALLS[0], bubble=bubble, z=z, f_star0_factor=1.1,
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
                bubble = Bubble(model=BAG, v_wall=v_wall, alpha_n=ALPHA)
                for i, beta_tilde in enumerate(BETA_TILDES):
                    ssm = spectrum(v_wall, bubble=bubble, beta_tilde=beta_tilde)
                    _, snr = ssm.power_spectrum(noise.f, noise=noise)
                    np.testing.assert_allclose(column.snr[i], snr, rtol=SNR_RTOL_PRECOMPUTED)
                    np.testing.assert_allclose(column.shock_times[i], ssm.H_star_eta_sh, rtol=1e-12)

    def test_export_column(self) -> None:
        """The exported spectra of an SNR grid column should match the spectra computed by PTPlot.

        The spectra are exported with the frequencies of the noise curve as the grid,
        and should share the fluid shell and the model of the column.
        The SNR of PTtools with only the instrument noise should match that of PTPlot with its default noise curve,
        and the spectra should be recreatable from the file.
        """
        noise = noise_curve()
        v_wall = V_WALLS[0]
        y = np.array([BETA_TILDE, 2 * BETA_TILDE])
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "spectra.h5"
            with Exporter(path, spectrum_fields=(Preset.MINIMAL, "snr_ins")) as exporter:
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
                np.testing.assert_allclose(importer.read(Table.SPECTRA_F, "snr_ins"), column.snr, rtol=1e-12)
                omgw0_h2 = importer.read(Table.SPECTRA_F, "omgw0_h2")
                loaded = importer.load_spectrum(0, table=Table.SPECTRA_F, parallel=False)
        assert isinstance(loaded, Spectrum)
        np.testing.assert_allclose(loaded.omgw0_h2(), omgw0_h2[0], rtol=1e-12)
        bubble = Bubble(model=BAG, v_wall=v_wall, alpha_n=ALPHA)
        for i, beta_tilde in enumerate(y):
            ssm = PowerSpectrumSSM(
                v_wall=v_wall, alpha=ALPHA, beta_tilde=beta_tilde, T_star=T_STAR, g_star=G_STAR, bubble=bubble
            )
            power_spectrum, _ = ssm.power_spectrum(noise.f, noise=noise)
            np.testing.assert_allclose(omgw0_h2[i], power_spectrum, rtol=1e-12)

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
