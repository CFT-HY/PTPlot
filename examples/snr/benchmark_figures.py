"""
Benchmark SNR figures
=====================

This scripts generates the SNR figures for all the benchmark models.
"""

# pylint: disable=broad-exception-caught, wrong-import-position

from datetime import timedelta
import logging
import os.path
import time

from django.db.models import Count
import numpy as np
from pandas import DataFrame
from pttools.speedup import MAX_WORKERS_DEFAULT

from examples.utils import setup_django

if __name__ == "__main__":
    setup_django()

from examples.utils import FIG_DIR, save_fig
from ptplot.models import Model
from ptplot.science import const
from ptplot.science.spectrum import Engine
from pttools.utils import IS_CFT_BIG_MACHINE

logger = logging.getLogger(__name__)


def main():
    start_time = time.perf_counter()
    models = Model.objects.prefetch_related("scenarios", "scenarios__points").annotate(n_points=Count("points"))
    n_models = len(models)

    # This is a heavy computation, so you may want to limit the number of workers on a shared system.
    max_workers = MAX_WORKERS_DEFAULT // 2 if IS_CFT_BIG_MACHINE else MAX_WORKERS_DEFAULT

    # Statistics
    n_spectra_engine = np.zeros((n_models, len(Engine)), dtype=np.int_)
    n_spectra_other = np.zeros_like(n_spectra_engine)
    times = np.zeros(n_models)
    times_engine = np.zeros((n_models, len(Engine)))

    for i_model, model in enumerate(models):
        model_start_time = time.perf_counter()
        logger.info("##### Processing model %d/%d: %s", i_model+1, n_models, model.name)
        for i_engine, engine in enumerate(Engine):
            engine_start_time = time.perf_counter()
            try:
                n_spectra_ab = const.DEFAULT_ALPHA_N_RANGE.size * const.DEFAULT_ALPHA_N_RANGE.size + model.n_points
                snr_ab = model.snr_figure_alpha_beta(engine=engine, max_workers=max_workers)
                save_fig(snr_ab, f"{model.slug}_snr_alpha_beta_{engine}")
                n_spectra_engine[i_model, i_engine] += n_spectra_ab
                snr_ab2 = model.snr_figure_alpha_beta(engine=engine, max_workers=max_workers, filled=True)
                save_fig(snr_ab2, f"{model.slug}_snr_alpha_beta_{engine}_filled")
                n_spectra_engine[i_model, i_engine] += n_spectra_ab
            except Exception as exc:
                logger.exception("Failed to plot snr_alpha_beta for %s", model.name, exc_info=exc)

            try:
                n_spectra_ur = const.DEFAULT_UBARF_RANGE.size * const.DEFAULT_UBARF_RANGE.size + model.n_points
                snr_ur = model.snr_figure_ubarf_rstar(engine=engine, max_workers=max_workers)
                save_fig(snr_ur, f"{model.slug}_snr_ubarf_rstar_{engine}")
                n_spectra_engine[i_model, i_engine] += n_spectra_ur
                snr_ur2 = model.snr_figure_ubarf_rstar(engine=engine, max_workers=max_workers, filled=True)
                save_fig(snr_ur2, f"{model.slug}_snr_ubarf_rstar_{engine}_filled")
                n_spectra_engine[i_model, i_engine] += n_spectra_ur
            except Exception as exc:
                logger.exception("Failed to plot snr_ubarf_rstar for %s", model.name, exc_info=exc)
            times_engine[i_model, i_engine] = time.perf_counter() - engine_start_time

        for i_engine, engine in enumerate((Engine.DBPL, Engine.SSM)):
            try:
                snr_comp = model.snr_comparison(engine1=Engine.BPL, engine2=engine, max_workers=max_workers)
                save_fig(snr_comp, f"{model.slug}_snr_comparison_{engine}")
                n_spectra_comp = const.DEFAULT_ALPHA_N_RANGE.size * const.DEFAULT_ALPHA_N_RANGE.size + model.n_points
                n_spectra_other[i_model, 0] += n_spectra_comp  # BPL
                n_spectra_other[i_model, i_engine+1] += n_spectra_comp  # DBPL / SSM
            except Exception as exc:
                logger.exception(
                    "Failed to plot snr_comparison_%s for %s",
                    engine.name, model.name,
                    exc_info=exc
                )

        try:
            snr_hist = model.snr_histogram()
            n_spectra_other[i_model, :] += model.n_points
            save_fig(snr_hist, f"{model.slug}_snr_histogram")
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
    times_ssm = times_engine[:, 2] / n_spectra[:, 2]
    df = DataFrame(
        data=
            {engine.upper(): n_spectra[:, i] for i, engine in enumerate(Engine)} |
            {f"{engine.upper()} time": times_engine[:, i] for i, engine in enumerate(Engine)} | {
                "total time": times,
                "SSM time / SSM spectrum": times_ssm,
                "SSM thread time / SSM spectrum": times_ssm * max_workers
        },
        index=[model.name for model in models]
    )
    df.to_csv(os.path.join(FIG_DIR, "benchmark_figures.csv"))


if __name__ == "__main__":
    main()
