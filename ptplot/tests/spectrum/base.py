"""Shared test case for the power spectrum classes.

The test classes of the individual power spectra should inherit from both
:class:`PowerSpectrumBaseCase` and :class:`unittest.TestCase`.
The base case does not inherit from :class:`unittest.TestCase` itself,
as then its tests would also be run for the abstract base case.
"""

from abc import ABC
from pathlib import Path
import tempfile
import typing as tp

import numpy as np
from pttools.export import Exporter, Extractor, Importer, Preset
import pytest

from ptplot.science.noise import noise_curve
from ptplot.science.plot.ps import power_spectrum_figure
from ptplot.science.spectrum import PowerSpectrum


class PowerSpectrumBaseCase[S: PowerSpectrum](ABC):
    """Tests that are run for each power spectrum class."""

    SPECTRUM_CLASS: type[S]
    V_WALL: tp.ClassVar[float] = 0.3
    ALPHA: tp.ClassVar[float] = 0.1
    BETA_TILDE: tp.ClassVar[float] = 10000
    T_STAR: tp.ClassVar[float] = 100
    G_STAR: tp.ClassVar[float] = 100
    #: Exported field that should match the SNR computed with the default noise curve
    SNR_FIELD: tp.ClassVar[str] = "snr"

    spectrum: S

    @classmethod
    def setUpClass(cls) -> None:
        """Create the power spectrum to be tested."""
        super().setUpClass()  # pyrefly: ignore[missing-attribute]
        cls.spectrum = cls.SPECTRUM_CLASS(
            T_star=cls.T_STAR, g_star=cls.G_STAR,
            v_wall=cls.V_WALL, alpha=cls.ALPHA, beta_tilde=cls.BETA_TILDE
        )

    @staticmethod
    def assert_positive(value: tp.Any) -> None:
        """Assert that all values are finite and positive."""
        arr = np.asarray(value)
        assert np.all(np.isfinite(arr)), f"Got non-finite values: {value}"
        assert np.all(arr > 0), f"Got non-positive values: {value}"

    def test_csv(self) -> None:
        """The power spectrum should be exportable as CSV."""
        assert self.spectrum.csv()

    def test_F_gw0_h2(self) -> None:
        r"""$F_{\text{gw},0} h^2$ should be finite and positive."""
        self.assert_positive(self.spectrum.F_gw0_h2())

    def test_h_star(self) -> None:
        """$h_*$ should be finite and positive."""
        self.assert_positive(self.spectrum.h_star())

    def test_H_star_eta_sh(self) -> None:
        r"""$\mathcal{H}_* \eta_\text{sh}$ should be finite and positive."""
        self.assert_positive(self.spectrum.H_star_eta_sh)

    def test_H_star_eta_v(self) -> None:
        r"""$\mathcal{H}_* \eta_\text{v}$ should be finite and positive."""
        self.assert_positive(self.spectrum.H_star_eta_v)

    def test_J(self) -> None:
        """$J$ should be finite and positive."""
        self.assert_positive(self.spectrum.J())

    def test_kinetic_energy(self) -> None:
        """The kinetic energy fraction $K$ should be finite and positive."""
        self.assert_positive(self.spectrum.kinetic_energy_fraction)

    def test_power_spectrum(self) -> None:
        """The power spectrum should be positive at the frequencies of the noise curve, and the SNR non-negative."""
        f = noise_curve().f
        power_spectrum, snr = self.spectrum.power_spectrum(f=f)
        assert power_spectrum.shape == f.shape
        self.assert_positive(power_spectrum)
        assert snr >= 0

    def test_ps_image(self) -> None:
        """The power spectrum figure should be created."""
        assert power_spectrum_figure(self.spectrum, sw_only=False) is not None

    def test_record(self) -> None:
        """The spectrum should have a record only after computing it."""
        spectrum = self.SPECTRUM_CLASS(
            T_star=self.T_STAR, g_star=self.G_STAR,
            v_wall=self.V_WALL, alpha=self.ALPHA, beta_tilde=self.BETA_TILDE
        )
        assert spectrum.record(Extractor()) is None
        spectrum.power_spectrum(f=noise_curve().f)
        assert spectrum.record(Extractor()) is not None

    def test_export(self) -> None:
        """The exported spectrum and its SNR should match the computed ones."""
        noise = noise_curve()
        power_spectrum, snr = self.spectrum.power_spectrum(f=noise.f, noise=noise)
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "spectra.h5"
            # The SNR is not in the minimal fields of the spectra of PTtools.
            with Exporter(path, spectrum_fields=(Preset.MINIMAL, self.SNR_FIELD)) as exporter:
                record = self.spectrum.record(exporter.extractor)
                assert record is not None
                exporter.add(record)
            with Importer(path, verify=True) as importer:
                assert importer.n_rows(record.table) == 1
                np.testing.assert_array_equal(importer.read(record.table, "f"), noise.f)
                np.testing.assert_allclose(importer.read(record.table, "omgw0_h2", 0), power_spectrum, rtol=1e-12)
                np.testing.assert_allclose(importer.read(record.table, self.SNR_FIELD, 0), snr, rtol=1e-12)

    def test_source_lifetime_factor(self) -> None:
        r"""The source lifetime factor $\Upsilon_\ell$ should be finite and positive."""
        self.assert_positive(self.spectrum.source_lifetime_factor())

    def test_f_star0_factor_unsupported(self) -> None:
        r"""The engines that do not use $f_{\ast,0}$ should reject ``f_star0_factor``."""
        if self.SPECTRUM_CLASS.SUPPORTS_F_STAR0_FACTOR:
            return
        with pytest.raises(ValueError, match="f_star0_factor"):
            self.SPECTRUM_CLASS(
                T_star=self.T_STAR, g_star=self.G_STAR,
                v_wall=self.V_WALL, alpha=self.ALPHA, beta_tilde=self.BETA_TILDE,
                f_star0_factor=2.
            )
