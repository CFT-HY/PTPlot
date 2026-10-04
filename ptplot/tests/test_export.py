"""Tests for exporting the spectra of the SNR computations with the exporter of PTtools."""

from pathlib import Path
import tempfile
import unittest
from unittest import mock

import numpy as np
from pttools.export import Exporter, Importer, Preset, Table

from ptplot.science import const
from ptplot.science.plot.snr_histogram import snr_histogram
from ptplot.science.snr.grid_alpha_beta import SNRGridAlphaBeta
from ptplot.science.snr.grid_ubarf_rstar import SNRGridUbarfRStar
from ptplot.science.spectrum.engine import Engine

ALPHA_N: np.ndarray = np.array([0.05, 0.1])
BETA_TILDE: np.ndarray = np.array([10., 100., 1000.])
UBARF: np.ndarray = np.array([0.05, 0.1])
R_STAR: np.ndarray = np.array([0.01, 0.1, 0.5])
#: The fields of the spectra in the tests. The SNR is used for matching the spectra to the grid.
SPECTRUM_FIELDS: tuple[Preset | str, ...] = (Preset.MINIMAL, "snr")


class ExportTest(unittest.TestCase):
    """Tests for exporting the spectra of the SNR grids and histograms."""

    def setUp(self) -> None:
        """Create a temporary directory for the exported files."""
        self.tmp_dir: tempfile.TemporaryDirectory[str] = tempfile.TemporaryDirectory()
        self.path: Path = Path(self.tmp_dir.name) / "spectra.h5"

    def tearDown(self) -> None:
        """Remove the temporary directory."""
        self.tmp_dir.cleanup()

    def assert_grid_exported(self, grid: SNRGridAlphaBeta | SNRGridUbarfRStar, y_name: str) -> None:
        """Assert that each point of the grid has been exported, and that the SNR values match.

        :param grid: SNR grid that has been computed with an exporter
        :param y_name: name of the field that corresponds to the y values of the grid
        """
        with Importer(self.path, verify=True) as importer:
            assert importer.n_spectra_f == grid.x.size * grid.y.size
            assert importer.n_spectra_y == 0
            # The fluid shell is computed once per column, and all the columns use the same model.
            assert importer.n_bubbles == grid.x.size
            assert importer.n_models == 1
            np.testing.assert_array_equal(importer.read(Table.SPECTRA_F, "f"), grid.noise.f)
            y = importer.read(Table.SPECTRA_F, y_name)
            snr = importer.read(Table.SPECTRA_F, "snr")
        # Each column of the grid has all the y values.
        np.testing.assert_allclose(np.sort(y), np.repeat(grid.y, grid.x.size), rtol=1e-12)
        np.testing.assert_allclose(np.sort(snr), np.sort(grid.snr.ravel()), rtol=1e-12)

    def test_grid_alpha_beta_ssm(self) -> None:
        r"""The spectra of an SSM grid in the $(\alpha_n, \beta/H)$ plane should be exported."""
        with Exporter(self.path, spectrum_fields=SPECTRUM_FIELDS) as exporter:
            grid = SNRGridAlphaBeta(
                T_star=const.DEFAULT_T_STAR, g_star=const.DEFAULT_G_STAR, v_wall=const.DEFAULT_V_WALL,
                alpha_n=ALPHA_N, beta_tilde=BETA_TILDE, engine=Engine.SSM,
                log_progress_percentage=None, max_workers=2, exporter=exporter
            )
        self.assert_grid_exported(grid, "beta_tilde")

    def test_grid_ubarf_rstar_ssm(self) -> None:
        r"""The spectra of an SSM grid in the $(\bar{U}_f, r_*)$ plane should be exported."""
        with Exporter(self.path, spectrum_fields=SPECTRUM_FIELDS) as exporter:
            grid = SNRGridUbarfRStar(
                T_star=const.DEFAULT_T_STAR, g_star=const.DEFAULT_G_STAR, v_wall=const.DEFAULT_V_WALL,
                ubarf=UBARF, r_star=R_STAR, engine=Engine.SSM,
                log_progress_percentage=None, max_workers=2, exporter=exporter
            )
        self.assert_grid_exported(grid, "r_star")

    def test_grid_analytic(self) -> None:
        """The spectra of an analytic engine should be exported to the table of the engine."""
        for engine in (Engine.BPL2020, Engine.BPL2024, Engine.DBPL2021, Engine.DBPL2024):
            with self.subTest(engine=engine):
                path = Path(self.tmp_dir.name) / f"{engine}.h5"
                with Exporter(path) as exporter:
                    grid = SNRGridAlphaBeta(
                        T_star=const.DEFAULT_T_STAR, g_star=const.DEFAULT_G_STAR, v_wall=const.DEFAULT_V_WALL,
                        alpha_n=ALPHA_N, beta_tilde=BETA_TILDE, engine=engine, exporter=exporter
                    )
                table = engine.spectrum.TABLE
                assert table is not None
                with Importer(path, verify=True) as importer:
                    assert set(importer.tables) == {*(str(tbl) for tbl in Table), table}
                    assert importer.n_rows(table) == grid.x.size * grid.y.size
                    assert importer.n_spectra_f == 0
                    assert importer.class_name(table) == f"{engine.spectrum.__module__}.{engine.spectrum.__qualname__}"
                    np.testing.assert_array_equal(importer.read(table, "f"), grid.noise.f)
                    params = importer.read_scalars(table, ("alpha", "beta_tilde", "snr"))
                # The analytic engines are computed point by point in the [y, x] order of the grid.
                np.testing.assert_allclose(params["alpha"], np.tile(grid.x, grid.y.size), rtol=1e-12)
                np.testing.assert_allclose(params["beta_tilde"], np.repeat(grid.y, grid.x.size), rtol=1e-12)
                np.testing.assert_allclose(params["snr"], grid.snr.ravel(), rtol=1e-12)

    def test_export_failure(self) -> None:
        """A failure in exporting should be logged without discarding the computed SNR values."""
        with Exporter(self.path) as exporter, \
                mock.patch.object(exporter, "add_many", side_effect=OSError("Disk full")), \
                self.assertLogs("ptplot.science.snr.point", level="ERROR"):
            grid = SNRGridAlphaBeta(
                T_star=const.DEFAULT_T_STAR, g_star=const.DEFAULT_G_STAR, v_wall=const.DEFAULT_V_WALL,
                alpha_n=ALPHA_N, beta_tilde=BETA_TILDE, engine=Engine.DEFAULT, exporter=exporter
            )
        assert np.all(np.isfinite(grid.snr))

    def test_histogram(self) -> None:
        """The spectra of the points of a histogram should be exported for each engine."""
        v_wall = np.array([0.5, 0.9])
        alpha_n = np.array([0.05, 0.1])
        beta_tilde = np.array([100., 1000.])
        with Exporter(self.path, spectrum_fields=SPECTRUM_FIELDS) as exporter:
            snr_histogram(
                v_wall=v_wall, alpha_n=alpha_n, beta_tilde=beta_tilde,
                T_star=np.full_like(v_wall, const.DEFAULT_T_STAR), g_star=np.full_like(v_wall, const.DEFAULT_G_STAR),
                engines=[Engine.DEFAULT, Engine.SSM], exporter=exporter
            )
        with Importer(self.path, verify=True) as importer:
            assert importer.n_spectra_f == v_wall.size
            assert importer.n_rows(Engine.DEFAULT.spectrum.TABLE or "") == v_wall.size
            assert importer.n_bubbles == v_wall.size
            assert importer.n_models == 1
            params = importer.read_scalars(Table.SPECTRA_F, ("v_wall", "alpha_n", "beta_tilde"))
        np.testing.assert_allclose(params["v_wall"], v_wall, rtol=1e-12)
        np.testing.assert_allclose(params["alpha_n"], alpha_n, rtol=1e-12)
        np.testing.assert_allclose(params["beta_tilde"], beta_tilde, rtol=1e-12)
