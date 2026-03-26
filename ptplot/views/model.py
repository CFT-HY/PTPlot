"""Views for models"""

from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest
from django.shortcuts import render

from ptplot.forms import BenchmarkForm
from ptplot.methods import fig_to_response, get_object_or_404_related
from ptplot.models import Model
from ptplot.science.spectrum import Engine


def models(request: HttpRequest) -> HttpResponse:
    """Display a list of models from database"""
    return render(request, "models.html", {"models": Model.objects.all()})


def model_detail(request: HttpRequest, model_id: int) -> HttpResponse:
    """Display a list of benchmark points for a model"""
    model: Model = get_object_or_404_related(
        Model,
        prefetch=["points", "scenarios"],
        id=model_id
    )
    form = BenchmarkForm(request.GET, model=model)
    if not form.is_valid():
        return HttpResponseBadRequest(f"Invalid form data: {request.GET}")
    return render(request, "model_detail.html", {"model": model, "form": form})


def model_detail_plot(request: HttpRequest, model_id: int) -> HttpResponse:
    """Display the benchmark points for a model on the SNR plots"""
    model: Model = get_object_or_404_related(
        Model,
        prefetch=["points", "scenarios"],
        id=model_id
    )
    form = BenchmarkForm(request.GET, model=model)
    if not form.is_valid():
        return HttpResponseBadRequest(f"Invalid form data: {request.GET}")
    return render(request, "model_detail_plot.html", {"model": model, "form": form})


def model_snr_alpha_beta(request: HttpRequest, model_id: int) -> HttpResponse:
    r"""Display the SNR values of the model points on the $(\alpha, \beta/H)$ plane"""
    model: Model = get_object_or_404_related(
        Model,
        prefetch=["scenarios", "scenarios__points"],
        pk=model_id
    )
    form = BenchmarkForm(request.GET, model=model)
    if not form.is_valid():
        return HttpResponseBadRequest(f"Invalid form data: {request.GET}")

    return fig_to_response(
        model.snr_figure_alpha_beta(mission_profile=form.mission_profile, engine=form.cleaned_data["engine"])
    )


def model_snr_comparison(request: HttpRequest, model_id: int) -> HttpResponse:
    """Compare the SNR of different engines for a model"""
    model: Model = get_object_or_404_related(
        Model,
        prefetch=["scenarios", "scenarios__points"],
        pk=model_id
    )
    form = BenchmarkForm(request.GET, model=model)
    if not form.is_valid():
        return HttpResponseBadRequest(f"Invalid form data: {request.GET}")

    engine = form.cleaned_data["engine"]
    return fig_to_response(
        model.snr_comparison(
            engine1=Engine.BPL,
            engine2=Engine.DBPL if engine == Engine.BPL else engine,
            mission_profile=form.mission_profile
        )
    )


def model_snr_histogram(request: HttpRequest, model_id: int) -> HttpResponse:
    """Display a histogram of the SNR values of the model points"""
    model: Model = get_object_or_404_related(
        Model,
        prefetch=["points"],
        id=model_id
    )
    form = BenchmarkForm(request.GET, model=model)
    if not form.is_valid():
        return HttpResponseBadRequest(f"Invalid form data: {request.GET}")

    return fig_to_response(
        model.snr_histogram(mission_profile=form.mission_profile)
    )


def model_snr_ubarf_rstar(request: HttpRequest, model_id: int) -> HttpResponse:
    r"""Display the SNR values of the model points on the $(\bar{U}_f, r_*)$ plane"""
    model: Model = get_object_or_404_related(
        Model,
        prefetch=["scenarios", "scenarios__points"],
        id=model_id
    )
    form = BenchmarkForm(request.GET, model=model)
    if not form.is_valid():
        return HttpResponseBadRequest(f"Invalid form data: {request.GET}")

    return fig_to_response(
        model.snr_figure_ubarf_rstar(mission_profile=form.mission_profile, engine=form.cleaned_data["engine"])
    )
