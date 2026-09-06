"""Views for images"""

from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest, HttpResponseNotAllowed

from ptplot.forms import PTPlotForm
from ptplot.methods import fig_to_response
from ptplot.science.plot.power_spectrum import power_spectrum_figure
from ptplot.science.plot.snr_alpha_beta import snr_figure_alpha_beta
from ptplot.science.plot.snr_ubarf_rstar import snr_figure_ubarf_rstar
from ptplot.science.snr_grid_alpha_beta import SNRGridAlphaBeta
from ptplot.science.snr_grid_ubarf_rstar import SNRGridUbarfRStar
from ptplot.science.spectrum.create import power_spectrum


def ps_image(request: HttpRequest) -> HttpResponse:
    """Power spectrum plot with sensitivity curve"""
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
        engine=form.cleaned_data["engine"]
    )
    fig = power_spectrum_figure(
        spectrum=spectrum,
        mission_profile=form.mission_profile,
    )
    return fig_to_response(fig)


def snr_alpha_beta(request: HttpRequest) -> HttpResponse:
    r"""SNR plot with $\alpha$ on the x-axis and $\beta/H$ on the y-axis"""
    if request.method != "GET":
        return HttpResponseNotAllowed(["GET"])

    form = PTPlotForm(request.GET)
    if not form.is_valid():
        return HttpResponseBadRequest()

    return fig_to_response(fig=snr_figure_alpha_beta(
        grid=SNRGridAlphaBeta(
            v_wall=form.cleaned_data["v_wall"],
            T_star=form.cleaned_data["T_star"],
            g_star=form.cleaned_data["g_star"],
            alpha_points=form.cleaned_data["alpha"],
            beta_over_H_points=form.cleaned_data["beta_over_H"],
            v_wall_points=form.cleaned_data["v_wall"],
            mission_profile=form.mission_profile,
            engine=form.cleaned_data["engine"]
        )
    ))


def snr_ubarf_rstar(request: HttpRequest) -> HttpResponse:
    """SNR plot with UbarF on the x-axis and H_n R_* on the y-axis"""
    if request.method != "GET":
        return HttpResponseNotAllowed(["GET"])

    form = PTPlotForm(request.GET)
    if not form.is_valid():
        return HttpResponseBadRequest()

    return fig_to_response(fig=snr_figure_ubarf_rstar(
        grid=SNRGridUbarfRStar(
            v_wall=form.cleaned_data["v_wall"],
            T_star=form.cleaned_data["T_star"],
            g_star=form.cleaned_data["g_star"],
            alpha_points=form.cleaned_data["alpha"],
            beta_over_H_points=form.cleaned_data["beta_over_H"],
            v_wall_points=form.cleaned_data["v_wall"],
            mission_profile=form.mission_profile,
            engine=form.cleaned_data["engine"]
        )
    ))
