"""Views for images"""

from django.http import HttpRequest, HttpResponse, HttpResponseNotAllowed, HttpResponseBadRequest

from ptplot.forms import PTPlotForm
from ptplot.methods import fig_to_response
from ptplot.science.spectrum.create import power_spectrum
from ptplot.science.plot.power_spectrum import ps_figure
from ptplot.science.plot.snr_alpha_beta import snr_figure_alpha_beta
from ptplot.science.plot.snr_ubarf_rstar import snr_figure_ubarf_rstar


def ps_image(request: HttpRequest) -> HttpResponse:
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
        engine=form.cleaned_data["engine"]
    )
    fig = ps_figure(
        spectrum=spectrum,
        mission_profile=form.mission_profile,
    )
    return fig_to_response(fig)


def snr_image(request: HttpRequest) -> HttpResponse:
    if request.method != "GET":
        return HttpResponseNotAllowed(["GET"])

    form = PTPlotForm(request.GET)
    if not form.is_valid():
        return HttpResponseBadRequest()

    fig = snr_figure_ubarf_rstar(
        T_star=form.cleaned_data["T_star"],
        g_star=form.cleaned_data["g_star"],
        vws=form.cleaned_data["vw"],
        alphas=form.cleaned_data["alpha"],
        beta_over_Hs=form.cleaned_data["beta_over_H"],
        mission_profile=form.mission_profile,
        engine=form.cleaned_data["engine"]
    )
    return fig_to_response(fig)


def snr_alphabeta_image(request: HttpRequest) -> HttpResponse:
    if request.method != "GET":
        return HttpResponseNotAllowed(["GET"])

    form = PTPlotForm(request.GET)
    if not form.is_valid():
        return HttpResponseBadRequest()

    fig = snr_figure_alpha_beta(
        v_wall=form.cleaned_data["vw"],
        alphas=form.cleaned_data["alpha"],
        beta_over_Hs=form.cleaned_data["beta_over_H"],
        T_star=form.cleaned_data["T_star"],
        g_star=form.cleaned_data["g_star"],
        mission_profile=form.mission_profile,
        engine=form.cleaned_data["engine"]
    )
    return fig_to_response(fig)
