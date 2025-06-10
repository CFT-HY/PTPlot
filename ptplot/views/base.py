import logging
import os

from django.http import HttpRequest, HttpResponse, HttpResponseNotAllowed, HttpResponseBadRequest
from django.shortcuts import render
import dulwich.porcelain
from dulwich.repo import Repo

from ptplot.forms import PTPlotForm
from ptplot.science.plot_powerspectrum import get_ps_data

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

    csv = get_ps_data(
        T_star=form.cleaned_data["T_star"],
        g_star=form.cleaned_data["g_star"],
        vw=form.cleaned_data["vw"],
        alpha=form.cleaned_data["alpha"],
        beta_over_H=form.cleaned_data["beta_over_H"],
        mission_profile=form.mission_profile
    )
    return HttpResponse(csv, content_type="text/csv")


def index(request: HttpRequest) -> HttpResponse:
    return render(
        request,
        "index.html",
        context={"git_description": GIT_DESCRIPTION} if HAVE_GITVER else None
    )
