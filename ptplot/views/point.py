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

    fig = snr_figure_alpha_beta(
        v_wall_snr=point.v_wall_value,
        T_star_snr=point.T_star_value,
        g_star_snr=point.g_star_value,
        alphas=point.alpha,
        beta_over_Hs=point.beta_over_H,
        labels=point.short_label,
        mission_profile=form.mission_profile,
        huge_alpha=point.model.huge_alpha,
        engine=form.cleaned_data["engine"]
    )
    return fig_to_response(fig)


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

    fig = snr_figure_ubarf_rstar(
        v_wall_snr=point.v_wall_value,
        T_star_snr=point.T_star_value,
        g_star_snr=point.g_star_value,
        alphas=point.alpha,
        beta_over_Hs=point.beta_over_H,
        v_walls=point.v_wall_value,
        labels=point.short_label,
        mission_profile=form.mission_profile,
        huge_alpha=point.model.huge_alpha,
        engine=form.cleaned_data["engine"]
    )
    return fig_to_response(fig)


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

    spectrum = power_spectrum(
        T_star=point.T_star_value,
        g_star=point.g_star_value,
        v_wall=point.v_wall_value,
        alpha=point.alpha,
        beta_over_H=point.beta_over_H,
        engine=form.cleaned_data["engine"]
    )
    csv = spectrum.csv(mission_profile=form.mission_profile)
    return HttpResponse(csv, content_type="text/csv")


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

    spectrum = power_spectrum(
        T_star=point.T_star_value,
        g_star=point.g_star_value,
        v_wall=point.v_wall_value,
        alpha=point.alpha,
        beta_over_H=point.beta_over_H,
        engine=form.cleaned_data["engine"]
    )
    fig = ps_figure(
        spectrum=spectrum,
        mission_profile=form.mission_profile
    )
    return fig_to_response(fig)
