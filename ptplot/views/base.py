"""Basic views."""

import logging

from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest, HttpResponseNotAllowed
from django.shortcuts import render

from ptplot.forms import PTPlotForm
from ptplot.science.spectrum.create import power_spectrum
from ptplot.science.utils import GIT_DESCRIPTION, HAVE_GITVER

logger = logging.getLogger(__name__)


def csv(request: HttpRequest) -> HttpResponse:
    """Get the power spectrum as a CSV file."""
    if request.method != "GET":
        return HttpResponseNotAllowed(["GET"])

    form = PTPlotForm(request.GET)
    if not form.is_valid():
        return HttpResponseBadRequest()

    spectrum = power_spectrum(
        T_star=form.cleaned_data["T_star"],
        g_star=form.cleaned_data["g_star"],
        v_wall=form.cleaned_data["v_wall"],
        alpha=form.cleaned_data["alpha"],
        beta_over_H=form.cleaned_data["beta_over_H"],
        engine=form.cleaned_data["engine"],
        css2=form.cleaned_data["css2"],
        csb2 = form.cleaned_data["csb2"]
    )
    csv_data = spectrum.csv(mission_profile=form.mission_profile)
    return HttpResponse(csv_data, content_type="text/csv")


def index(request: HttpRequest) -> HttpResponse:
    """Index page."""
    return render(
        request,
        "index.html",
        context={"git_description": GIT_DESCRIPTION} if HAVE_GITVER else None
    )
