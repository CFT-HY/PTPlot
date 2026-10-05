"""
Benchmark SNR figures
=====================

This scripts generates the SNR figures for all the benchmark models.
Running this script can take several hours.

The computed spectra are exported to the HDF5 file ``benchmark_spectra.h5`` in the figure directory
with :py:class:`pttools.export.exporter.Exporter`.
The spectra of the SNR grids are exported only for the engines of :py:data:`EXPORT_ENGINES`,
and the spectra of the histograms for all the engines.
The spectra have all been computed at the frequencies of the default noise curve.
The spectra of the Sound Shell Model (SSM) are in the table :py:attr:`pttools.export.records.Table.SPECTRA_F`,
and the spectra of the other engines in the tables of the engines,
see :py:attr:`ptplot.science.spectrum.base.PowerSpectrum.TABLE`.
The rows of the spectra of each model, figure and table are listed in ``benchmark_spectra.csv``.
The file can be read with :py:class:`pttools.export.importer.Importer`.
"""

from collections.abc import Iterator
import contextlib
from datetime import timedelta
import logging
import time
import typing as tp

from django.db.models import Count
import numpy as np
from pandas import DataFrame
from pttools.export import Exporter, Preset

from examples.utils import FIG_DIR, save_model_fig
from ptplot.methods import setup_django

if __name__ == "__main__":
    setup_django()

from ptplot.methods import n_workers
from ptplot.models import Model
from ptplot.science import const
from ptplot.science.snr.grid_alpha_beta import SNRGridAlphaBeta
from ptplot.science.spectrum import Engine

logger: logging.Logger = logging.getLogger(__name__)

#: Path of the HDF5 file of the exported spectra
SPECTRA_PATH = FIG_DIR / "benchmark_spectra.h5"
#: Path of the CSV file that lists the rows of the exported spectra of each model, figure and table
SPECTRA_INDEX_PATH = FIG_DIR / "benchmark_spectra.csv"
#: The engines whose spectra of the SNR grids are exported.
#: The spectra of the analytic engines can be recomputed in milliseconds,
#: and exporting all of them would make the file several gigabytes.
EXPORT_ENGINES: tuple[Engine, ...] = (Engine.SSM,)
#: The fields of the exported spectra in addition to the minimal and the importable ones.
#: ``snr`` is computed with the default noise curve of PTtools, which includes the compact binary noises,
#: and ``snr_ins`` with only the instrument noise, which is the default noise curve of PTPlot.
SPECTRUM_FIELDS: tuple[Preset | str, ...] = (
    Preset.MINIMAL, "snr", "snr_ins", "H_star_eta_sh", "ubarf2", "omgw0_peak_f", "omgw0_peak"
)


@contextlib.contextmanager
def spectra_rows(index: list[dict[str, tp.Any]], exporter: Exporter, **info: tp.Any) -> Iterator[None]:
    """Record the rows of the spectra that are exported within the context.

    The rows are recorded also if an exception is raised, as the spectra exported before it remain in the file.

    :param index: List to which the row range of each table is appended, if any spectra were exported to it
    :param exporter: Exporter of the spectra
    :param info: Information about the spectra, e.g. the model and the figure
    """
    start = {table: exporter.n_rows(table) for table in exporter.tables}
    try:
        yield
    finally:
        for table in exporter.tables:
            first_row = start.get(table, 0)
            n_rows = exporter.n_rows(table) - first_row
            if n_rows > 0:
                index.append({**info, "table": table, "first_row": first_row, "n_rows": n_rows})


def main() -> None:
    """Create the SNR figures for all the benchmark models, and export the SSM spectra."""
    spectra_index: list[dict[str, tp.Any]] = []
    try:
        with Exporter(SPECTRA_PATH, mode="w", spectrum_fields=SPECTRUM_FIELDS) as exporter:
            create_figures(exporter, spectra_index)
    finally:
        # The index is written after the exporter has been closed, i.e. after the last rows have been written.
        DataFrame(spectra_index).to_csv(SPECTRA_INDEX_PATH, index=False)


def create_figures(exporter: Exporter, spectra_index: list[dict[str, tp.Any]]) -> None:  # noqa: PLR0915
    """Create the SNR figures for all the benchmark models.

    :param exporter: Exporter to which the computed spectra are added
    :param spectra_index: List to which the rows of the exported spectra of each model and figure are appended
    """
    start_time = time.perf_counter()
    models = Model.objects.prefetch_related("scenarios", "scenarios__points").annotate(n_points=Count("points"))
    n_models = len(models)
    engines = Engine.engines(fast=True, log=True)
    engines_non_default = Engine.non_default(fast=True)

    # This is a heavy computation, so you may want to limit the number of workers on a shared system.
    max_workers = n_workers()
    logger.info("Creating benchmark figures with %d parallel workers.", max_workers)

    # Statistics
    n_spectra_engine = np.zeros((n_models, len(engines)), dtype=np.int_)
    n_spectra_other = np.zeros_like(n_spectra_engine)
    times = np.zeros(n_models)
    times_engine = np.zeros((n_models, len(engines)))

    model: Model
    for i_model, model in enumerate(models):
        model_start_time = time.perf_counter()
        logger.info("##### Processing model %d/%d: %s", i_model+1, n_models, model.name)
        snr_abs: dict[Engine, SNRGridAlphaBeta] = {}
        for i_engine, engine in enumerate(engines):
            engine_start_time = time.perf_counter()
            try:
                n_spectra_ab = const.DEFAULT_ALPHA_N_RANGE.size * const.DEFAULT_ALPHA_N_RANGE.size + model.n_points
                with spectra_rows(spectra_index, exporter, model=model.name, figure="snr_alpha_beta"):
                    snr_ab = model.snr_grid_alpha_beta(
                        engine=engine, max_workers=max_workers,
                        exporter=exporter if engine in EXPORT_ENGINES else None
                    )
                snr_abs[engine] = snr_ab
                n_spectra_engine[i_model, i_engine] += n_spectra_ab
                snr_ab_fig = model.snr_figure_alpha_beta(grid=snr_ab)
                save_model_fig(snr_ab_fig, model, f"snr_alpha_beta_{engine}")
                snr_ab_fig2 = model.snr_figure_alpha_beta(grid=snr_ab, filled=True)
                save_model_fig(snr_ab_fig2, model, f"snr_alpha_beta_{engine}_filled")
            except Exception as exc:
                logger.exception("Failed to plot snr_alpha_beta for %s", model.name, exc_info=exc)

            try:
                n_spectra_ur = const.DEFAULT_UBARF_RANGE.size * const.DEFAULT_UBARF_RANGE.size + model.n_points
                with spectra_rows(spectra_index, exporter, model=model.name, figure="snr_ubarf_rstar"):
                    snr_ur = model.snr_grid_ubarf_rstar(
                        engine=engine, max_workers=max_workers,
                        exporter=exporter if engine in EXPORT_ENGINES else None
                    )
                n_spectra_engine[i_model, i_engine] += n_spectra_ur
                snr_ur_fig = model.snr_figure_ubarf_rstar(grid=snr_ur)
                save_model_fig(snr_ur_fig, model, f"snr_ubarf_rstar_{engine}")
                snr_ur_fig2 = model.snr_figure_ubarf_rstar(grid=snr_ur, filled=True)
                save_model_fig(snr_ur_fig2, model, f"snr_ubarf_rstar_{engine}_filled")
            except Exception as exc:
                logger.exception("Failed to plot snr_ubarf_rstar for %s", model.name, exc_info=exc)
            times_engine[i_model, i_engine] = time.perf_counter() - engine_start_time

        for engine in engines_non_default:
            try:
                snr_comp = model.snr_comparison(grid1=snr_abs[Engine.DEFAULT], grid2=snr_abs[engine])
                save_model_fig(snr_comp, model, f"snr_comparison_{engine}")
            except Exception as exc:
                logger.exception(
                    "Failed to plot snr_comparison_%s for %s",
                    engine.name, model.name,
                    exc_info=exc
                )

        try:
            with spectra_rows(spectra_index, exporter, model=model.name, figure="snr_histogram"):
                snr_hist = model.snr_histogram(engines=engines, exporter=exporter)
            n_spectra_other[i_model, :] += model.n_points
            save_model_fig(snr_hist, model, "snr_histogram")
        except Exception as exc:
            logger.exception("Failed to plot snr_histogram for %s", model.name, exc_info=exc)

        model_time = time.perf_counter() - model_start_time
        times[i_model] = model_time
        logger.info(
            "Processed model %d/%d: %s, took %.2f s",
            i_model+1, n_models, model.name, model_time
        )

    total_time = time.perf_counter() - start_time
    logger.info(
        "Processed %d models, took %s s, %.2f s per model.",  # Bubble cache info: %s
        n_models, timedelta(seconds=total_time), total_time / n_models,
        # bubble.cache_info()
    )

    n_spectra = n_spectra_engine + n_spectra_other
    if Engine.SSM in engines:
        i_ssm = engines.index(Engine.SSM)
        times_ssm = times_engine[:, i_ssm] / n_spectra[:, i_ssm]
        ssm_dict = {
            "SSM time / SSM spectrum": times_ssm,
            "SSM thread time / SSM spectrum": times_ssm * max_workers
        }
    else:
        ssm_dict = {}
    df = DataFrame(
        data=
            {engine.upper(): n_spectra[:, i] for i, engine in enumerate(engines)} |
            {f"{engine.upper()} time": times_engine[:, i] for i, engine in enumerate(engines)} |
            {"total time": times} |
            ssm_dict,
        index=[model.name for model in models]
    )
    df.to_csv(FIG_DIR / "benchmark_figures.csv")


if __name__ == "__main__":
    main()
