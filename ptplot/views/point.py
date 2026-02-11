"""Views for points"""

from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest
from django.shortcuts import render

from ptplot.forms import BenchmarkForm
from ptplot.methods import fig_to_response, get_object_or_404_related
from ptplot.models import ParameterChoice
from ptplot.science.plot.power_spectrum import ps_figure
from ptplot.science.plot.snr_alpha_beta import snr_figure_alpha_beta
from ptplot.science.plot.snr_ubarf_rstar import snr_figure_ubarf_rstar
from ptplot.science.spectrum.create import power_spectrum


def model_point_plot(request: HttpRequest, model_id: int, point_id: int) -> HttpResponse:
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


def model_point_snr(request: HttpRequest, model_id: int, point_id: int) -> HttpResponse:
    point: ParameterChoice = get_object_or_404_related(
        ParameterChoice,
        related=["model"],
        model__id=model_id,
        number=point_id
    )
    form = BenchmarkForm(request.GET, point=point)
    if not form.is_valid():
        return HttpResponseBadRequest(f"Invalid form data: {request.GET}")

    fig = snr_figure_ubarf_rstar(
        T_star=point.T_star_value,
        g_star=point.g_star_value,
        vws=point.vw_value,
        alphas=point.alpha,
        beta_over_Hs=point.beta_over_H,
        labels=point.short_label,
        mission_profile=form.mission_profile,
        huge_alpha=point.model.huge_alpha,
        engine=form.cleaned_data["engine"]
    )
    return fig_to_response(fig)


def model_point_snr_alphabeta(request: HttpRequest, model_id: int, point_id: int) -> HttpResponse:
    point: ParameterChoice = get_object_or_404_related(
        ParameterChoice,
        related=["model"],
        model__id=model_id,
        number=point_id
    )
    form = BenchmarkForm(request.GET, point=point)
    if not form.is_valid():
        return HttpResponseBadRequest(f"Invalid form data: {request.GET}")

    fig = snr_figure_alpha_beta(
        T_star=point.T_star_value,
        g_star=point.g_star_value,
        v_wall=point.vw_value,
        alphas=point.alpha,
        beta_over_Hs=point.beta_over_H,
        labels=point.short_label,
        mission_profile=form.mission_profile,
        huge_alpha=point.model.huge_alpha,
        engine=form.cleaned_data["engine"]
    )
    return fig_to_response(fig)


def model_point_csv(request: HttpRequest, model_id: int, point_id: int) -> HttpResponse:
    point: ParameterChoice = get_object_or_404_related(
        ParameterChoice,
        related=["model"],
        model__id=model_id,
        number=point_id
    )
    form = BenchmarkForm(request.GET, point=point)
    if not form.is_valid():
        return HttpResponseBadRequest(f"Invalid form data: {request.GET}")

    spectrum = power_spectrum(
        T_star=point.T_star_value,
        g_star=point.g_star_value,
        vw=point.vw_value,
        alpha=point.alpha,
        beta_over_H=point.beta_over_H,
        engine=form.cleaned_data["engine"]
    )
    csv = spectrum.csv(mission_profile=form.mission_profile)
    return HttpResponse(csv, content_type="text/csv")


def model_point_ps(request: HttpRequest, model_id: int, point_id: int) -> HttpResponse:
    point: ParameterChoice = get_object_or_404_related(
        ParameterChoice,
        related=["model"],
        model__id=model_id,
        number=point_id
    )
    form = BenchmarkForm(request.GET, point=point)
    if not form.is_valid():
        return HttpResponseBadRequest(f"Invalid form data: {request.GET}")

    spectrum = power_spectrum(
        T_star=point.T_star_value,
        g_star=point.g_star_value,
        vw=point.vw_value,
        alpha=point.alpha,
        beta_over_H=point.beta_over_H,
        engine=form.cleaned_data["engine"]
    )
    fig = ps_figure(
        spectrum=spectrum,
        mission_profile=form.mission_profile
    )
    return fig_to_response(fig)
