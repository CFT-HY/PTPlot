"""Views for points"""

from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest
from django.shortcuts import render

from ptplot.forms import BenchmarkForm
from ptplot.methods import fig_to_response, get_object_or_404_related
from ptplot.models import ParameterChoice
from ptplot.science.spectrum import Engine


def model_point_plot(request: HttpRequest, model_id: int, point_id: int) -> HttpResponse:
    """Display an individual model point on the SNR and PS plots"""
    point: ParameterChoice = get_object_or_404_related(
        ParameterChoice,
        related=["model"],
        prefetch=["model__points", "model__scenarios"],
        model__id=model_id,
        number=point_id
    )
    form = BenchmarkForm(request.GET, point=point)
    if not form.is_valid():
        return HttpResponseBadRequest(f"Invalid form data: {request.GET}")
    return render(
        request,
        "model_point_plot.html",
        {"model": point.model, "point": point, "form": form}
    )


def model_point_snr_alpha_beta(request: HttpRequest, model_id: int, point_id: int) -> HttpResponse:
    r"""Display an individual model point on the $\alpha, \beta/H$ SNR plot"""
    point: ParameterChoice = get_object_or_404_related(
        ParameterChoice,
        related=["model"],
        model__id=model_id,
        number=point_id
    )
    form = BenchmarkForm(request.GET, point=point)
    if not form.is_valid():
        return HttpResponseBadRequest(f"Invalid form data: {request.GET}")

    return fig_to_response(
        point.snr_figure_alpha_beta(mission_profile=form.mission_profile, engine=form.cleaned_data["engine"])
    )


def model_point_snr_comparison(request: HttpRequest, model_id: int, point_id: int) -> HttpResponse:
    r"""Compare the SNR of different engines for a model point"""
    point: ParameterChoice = get_object_or_404_related(
        ParameterChoice,
        related=["model"],
        model__id=model_id,
        number=point_id
    )
    form = BenchmarkForm(request.GET, point=point)
    if not form.is_valid():
        return HttpResponseBadRequest(f"Invalid form data: {request.GET}")

    engine = form.cleaned_data["engine"]
    return fig_to_response(
        point.snr_comparison(
            engine1=Engine.BPL,
            engine2=Engine.DBPL if engine == Engine.BPL else engine,
            mission_profile=form.mission_profile
        )
    )


def model_point_snr_ubarf_rstar(request: HttpRequest, model_id: int, point_id: int) -> HttpResponse:
    r"""Display an individual model point on the $\bar{U}_f, r_*$ SNR plot"""
    point: ParameterChoice = get_object_or_404_related(
        ParameterChoice,
        related=["model"],
        model__id=model_id,
        number=point_id
    )
    form = BenchmarkForm(request.GET, point=point)
    if not form.is_valid():
        return HttpResponseBadRequest(f"Invalid form data: {request.GET}")

    return fig_to_response(
        point.snr_figure_ubarf_rstar(mission_profile=form.mission_profile, engine=form.cleaned_data["engine"])
    )


def model_point_csv(request: HttpRequest, model_id: int, point_id: int) -> HttpResponse:
    """Get the CSV data of a model point"""
    point: ParameterChoice = get_object_or_404_related(
        ParameterChoice,
        related=["model"],
        model__id=model_id,
        number=point_id
    )
    form = BenchmarkForm(request.GET, point=point)
    if not form.is_valid():
        return HttpResponseBadRequest(f"Invalid form data: {request.GET}")

    return HttpResponse(
        point.csv(mission_profile=form.mission_profile, engine=form.cleaned_data["engine"]),
        content_type="text/csv"
    )


def model_point_ps(request: HttpRequest, model_id: int, point_id: int) -> HttpResponse:
    """Display the power spectrum of an individual model point"""
    point: ParameterChoice = get_object_or_404_related(
        ParameterChoice,
        related=["model"],
        model__id=model_id,
        number=point_id
    )
    form = BenchmarkForm(request.GET, point=point)
    if not form.is_valid():
        return HttpResponseBadRequest(f"Invalid form data: {request.GET}")

    return fig_to_response(
        point.power_spectrum_figure(mission_profile=form.mission_profile, engine=form.cleaned_data["engine"])
    )
