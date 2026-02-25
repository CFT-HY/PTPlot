"""
Benchmark SNR figures
=====================

This scripts generates the SNR figures for all the benchmark models.
"""

# pylint: disable=broad-exception-caught, wrong-import-position

import logging

from django.http import HttpRequest

from examples.utils import save_svg_response, setup_django

if __name__ == "__main__":
    setup_django()

from ptplot.forms import BenchmarkForm
from ptplot.models import Model
from ptplot.science.spectrum import Engine, bubble
from ptplot.views.model import model_snr_alpha_beta, model_snr_histogram, model_snr_ubarf_rstar

logger = logging.getLogger(__name__)


def main():
    models = Model.objects.all()
    n_models = len(models)
    for i, model in enumerate(models):
        print(f"Processing model {i+1}/{n_models}: {model.name}")
        for engine in Engine:
            form = BenchmarkForm({"engine": engine}, model=model)
            form.is_valid()
            request = HttpRequest()
            request.GET.update(form.cleaned_data)

            try:
                snr_ab = model_snr_alpha_beta(request, model.id)
                save_svg_response(snr_ab, f"{model.slug}_snr_alpha_beta_{engine}")
            except Exception as exc:
                logger.exception("Failed to plot snr_alpha_beta for %s", model.name, exc_info=exc)

            try:
                snr_ur = model_snr_ubarf_rstar(request, model.id)
                save_svg_response(snr_ur, f"{model.slug}_snr_ubarf_rstar_{engine}")
            except Exception as exc:
                logger.exception("Failed to plot snr_ubarf_rstar for %s", model.name, exc_info=exc)

        request = HttpRequest()
        try:
            snr_hist = model_snr_histogram(request, model.id)
            save_svg_response(snr_hist, f"{model.slug}_snr_histogram")
        except Exception as exc:
            logger.exception("Failed to plot snr_histogram for %s", model.name, exc_info=exc)

    print(bubble.cache_info())


if __name__ == "__main__":
    main()
