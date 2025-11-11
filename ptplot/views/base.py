import logging
import os

from django.http import HttpRequest, HttpResponse, HttpResponseNotAllowed, HttpResponseBadRequest
from django.shortcuts import render
import dulwich.porcelain
from dulwich.repo import Repo

from ptplot.forms import PTPlotForm
from ptplot.science.spectrum.create import power_spectrum

logger = logging.getLogger(__name__)
GIT_DESCRIPTION: str = "unknown"
HAVE_GITVER: bool = False

try:
     THIS_FILE_DIR = os.path.realpath(os.path.dirname(__file__))
     GIT_DESCRIPTION = dulwich.porcelain.describe(Repo.discover(THIS_FILE_DIR))
     HAVE_GITVER = True
except dulwich.errors.NotGitRepository as err:
     logger.exception("Could not load git repository info.", exc_info=err)


def csv(request: HttpRequest) -> HttpResponse:
    if request.method != "GET":
        return HttpResponseNotAllowed(["GET"])

    form = PTPlotForm(request.GET)
    if not form.is_valid():
        return HttpResponseBadRequest()

    spectrum = power_spectrum(
        T_star=form.cleaned_data["T_star"],
        g_star=form.cleaned_data["g_star"],
        vw=form.cleaned_data["vw"],
        alpha=form.cleaned_data["alpha"],
        beta_over_H=form.cleaned_data["beta_over_H"],
        engine=form.cleaned_data["engine"],
        css2=form.cleaned_data["css2"],
        csb2 = form.cleaned_data["csb2"]
    )
    csv_data = spectrum.csv(mission_profile=form.mission_profile)
    return HttpResponse(csv_data, content_type="text/csv")


def index(request: HttpRequest) -> HttpResponse:
    return render(
        request,
        "index.html",
        context={"git_description": GIT_DESCRIPTION} if HAVE_GITVER else None
    )
