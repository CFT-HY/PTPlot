"""
Benchmark SNR figures
=====================

This scripts generates the SNR figures for all the benchmark models.
"""

# pylint: disable=broad-exception-caught, wrong-import-position

import logging

from examples.utils import setup_django

if __name__ == "__main__":
    setup_django()

from examples.utils import save
from ptplot.models import Model
from ptplot.science.spectrum import Engine, bubble

logger = logging.getLogger(__name__)


def main():
    models = Model.objects.all()
    n_models = len(models)
    for i, model in enumerate(models):
        logger.info(f"Processing model {i+1}/{n_models}: {model.name}")
        for engine in Engine:
            try:
                snr_ab = model.snr_figure_alpha_beta(engine=engine)
                save(snr_ab, f"{model.slug}_snr_alpha_beta_{engine}")
            except Exception as exc:
                logger.exception("Failed to plot snr_alpha_beta for %s", model.name, exc_info=exc)

            try:
                snr_ur = model.snr_figure_ubarf_rstar(engine=engine)
                save(snr_ur, f"{model.slug}_snr_ubarf_rstar_{engine}")
            except Exception as exc:
                logger.exception("Failed to plot snr_ubarf_rstar for %s", model.name, exc_info=exc)

        for engine in (Engine.DBPL, Engine.SSM):
            try:
                snr_comp = model.snr_comparison(Engine.BPL, engine)
                save(snr_comp, f"{model.slug}_snr_comparison_{engine.name}")
            except Exception as exc:
                logger.exception(
                    "Failed to plot snr_comparison_%s for %s",
                    engine.name, model.name,
                    exc_info=exc
                )

        try:
            snr_hist = model.snr_histogram()
            save(snr_hist, f"{model.slug}_snr_histogram")
        except Exception as exc:
            logger.exception("Failed to plot snr_histogram for %s", model.name, exc_info=exc)

    logger.debug(bubble.cache_info())


if __name__ == "__main__":
    main()
