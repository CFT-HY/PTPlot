"""Views for models"""

from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest
from django.shortcuts import render
import numpy as np

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


def model_snr_ubarf_rstar(request: HttpRequest, model_id: int) -> HttpResponse:
    model: Model = get_object_or_404_related(
        Model,
        prefetch=["scenarios"],
        id=model_id
    )
    form = BenchmarkForm(request.GET, model=model)
    if not form.is_valid():
        return HttpResponseBadRequest(f"Invalid form data: {request.GET}")

    if model.has_scenarios:
        scenarios = model.scenarios.prefetch_related("points").all()
        vws = []
        alphas = []
        beta_over_Hs = []
        labels = []
        titles = []

        for scenario in scenarios:
            points = scenario.points.all()
            vws.append(np.array([model.vw if point.vw is None else point.vw for point in points]))
            alphas.append(np.array([point.alpha for point in points]))
            beta_over_Hs.append(np.array([point.beta_over_H for point in points]))
            labels.append([point.short_label for point in points])
            titles.append(scenario.name)
    else:
        points = model.points.all()
        vws = np.array([model.vw if point.vw is None else point.vw for point in points])
        alphas = np.array([point.alpha for point in points])
        beta_over_Hs = np.array([point.beta_over_H for point in points])
        labels = [point.short_label for point in points]
        titles = model.name

    fig = snr_figure_ubarf_rstar(
        v_wall_snr=model.vw,
        v_walls=vws,
        alphas=alphas,
        beta_over_Hs=beta_over_Hs,
        T_star=model.T_star,
        g_star=model.g_star,
        labels=labels,
        titles=titles,
        mission_profile=model.mission_profile,
        huge_alpha=model.huge_alpha,
        engine=form.cleaned_data["engine"]
    )
    return fig_to_response(fig)


def model_snr_alpha_beta(request: HttpRequest, model_id: int) -> HttpResponse:
    model: Model = get_object_or_404_related(
        Model,
        prefetch=["scenarios"],
        pk=model_id
    )
    form = BenchmarkForm(request.GET, model=model)
    if not form.is_valid():
        return HttpResponseBadRequest(f"Invalid form data: {request.GET}")

    if model.has_scenarios:
        scenarios = model.scenarios.prefetch_related("points").all()
        alphas = []
        beta_over_Hs = []
        labels = []
        titles = []

        for scenario in scenarios:
            points = scenario.points.all()
            alphas.append([point.alpha for point in points])
            beta_over_Hs.append([point.beta_over_H for point in points])
            labels.append([point.short_label for point in points])
            titles.append(scenario.name)

    else:
        points = model.points.all()
        alphas = [point.alpha for point in points]
        beta_over_Hs = [point.beta_over_H for point in points]
        labels = [point.short_label for point in points]
        titles = model.name

    fig = snr_figure_alpha_beta(
        v_wall_snr=model.vw,
        alphas=alphas,
        beta_over_Hs=beta_over_Hs,
        T_star=model.T_star,
        g_star=model.g_star,
        labels=labels,
        titles=titles,
        mission_profile=model.mission_profile,
        huge_alpha=model.huge_alpha,
        engine=form.cleaned_data["engine"]
    )
    return fig_to_response(fig)
