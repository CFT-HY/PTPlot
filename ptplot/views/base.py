"""Basic views."""

import logging

from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest, HttpResponseNotAllowed
from django.shortcuts import render

from ptplot.forms import PTPlotForm
from ptplot.science.spectrum.create import power_spectrum
from ptplot.science.utils import GIT_DESCRIPTION, HAVE_GITVER
from ptplot.views.validation import validate_forms

logger: logging.Logger = logging.getLogger(__name__)


def csv(request: HttpRequest) -> HttpResponse:
    """Get the power spectrum as a CSV file."""
    if request.method != "GET":
        return HttpResponseNotAllowed(["GET"])

    validated = validate_forms(request, PTPlotForm)
    if isinstance(validated, HttpResponseBadRequest):
        return validated
    form = validated.form

    spectrum = power_spectrum(
        T_star=form.cleaned_data["T_star"],
        g_star=form.cleaned_data["g_star"],
        v_wall=form.cleaned_data["v_wall"],
        alpha=form.cleaned_data["alpha"],
        beta_tilde=form.cleaned_data["beta_tilde"],
        engine=form.cleaned_data["engine"],
        model=form.model,
        legacy_nucleation_cs_max=form.cleaned_data["legacy_nucleation_cs_max"],
        ssm_settings=validated.ssm_settings
    )
    csv_data = spectrum.csv(noise=form.noise)
    return HttpResponse(csv_data, content_type="text/csv")


def index(request: HttpRequest) -> HttpResponse:
    """Index page."""
    return render(
        request,
        "index.html",
        context={"git_description": GIT_DESCRIPTION} if HAVE_GITVER else None
    )
