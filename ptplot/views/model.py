"""Views for models"""

from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest
from django.shortcuts import render

from ptplot.forms import BenchmarkForm
from ptplot.methods import fig_to_response, get_object_or_404_related
from ptplot.models import Model
from ptplot.science.plot.snr_alpha_beta import snr_figure_alpha_beta
from ptplot.science.plot.snr_ubarf_rstar import snr_figure_ubarf_rstar


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
    model: Model = get_object_or_404_related(
        Model,
        prefetch=["scenarios"],
        pk=model_id
    )
    form = BenchmarkForm(request.GET, model=model)
    if not form.is_valid():
        return HttpResponseBadRequest(f"Invalid form data: {request.GET}")

    v_walls, alphas, beta_over_Hs, labels, titles = model.point_data_by_field()
    fig = snr_figure_alpha_beta(
        v_wall_snr=model.v_wall,
        T_star_snr=model.T_star,
        g_star_snr=model.g_star,
        alphas=alphas,
        beta_over_Hs=beta_over_Hs,
        labels=labels,
        titles=titles,
        mission_profile=model.mission_profile,
        huge_alpha=model.huge_alpha,
        engine=form.cleaned_data["engine"]
    )
    return fig_to_response(fig)


def model_snr_ubarf_rstar(request: HttpRequest, model_id: int) -> HttpResponse:
    model: Model = get_object_or_404_related(
        Model,
        prefetch=["scenarios"],
        id=model_id
    )
    form = BenchmarkForm(request.GET, model=model)
    if not form.is_valid():
        return HttpResponseBadRequest(f"Invalid form data: {request.GET}")

    v_walls, alphas, beta_over_Hs, labels, titles = model.point_data_by_field()
    fig = snr_figure_ubarf_rstar(
        v_wall_snr=model.v_wall,
        T_star_snr=model.T_star,
        g_star_snr=model.g_star,
        v_walls=v_walls,
        alphas=alphas,
        beta_over_Hs=beta_over_Hs,
        labels=labels,
        titles=titles,
        mission_profile=model.mission_profile,
        huge_alpha=model.huge_alpha,
        engine=form.cleaned_data["engine"]
    )
    return fig_to_response(fig)
