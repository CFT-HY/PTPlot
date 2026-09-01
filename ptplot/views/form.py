"""Views for forms"""

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from ptplot.forms import MultipleForm, ParameterChoiceForm, PTPlotForm
from ptplot.methods import fig_to_response, get_object_or_404_related
from ptplot.models import Model
from ptplot.science.spectrum.engine import ENGINE_NAMES
from ptplot.science.plot.snr_alpha_beta import snr_figure_alpha_beta
from ptplot.science.snr_grid_alpha_beta import SNRGridAlphaBeta


def multiple(request: HttpRequest) -> HttpResponse:
    """Plot many points - manual input"""
    if request.method == "POST":
        form = MultipleForm(request.POST)

        if form.is_valid():
            # querystring = request.GET.urlencode()
            # usetex = form.cleaned_data["usetex"]

            table_lines = form.cleaned_data["table"].splitlines()
            alphas = []
            beta_over_Hs = []
            labels = []

            read_lines = 0

            for line in table_lines:
                line = line.strip()
                if len(line) == 0 or line[0] == "#":
                    continue

                read_lines += 1

                bits = line.split(",")
                alphas.append(float(bits[0]))
                beta_over_Hs.append(float(bits[1]))
                try:
                    labels.append(bits[2].strip())
                except IndexError:
                    pass

            if not len(labels) == read_lines:
                label_list_final = None
            else:
                label_list_final = [labels]

            fig = snr_figure_alpha_beta(
                grid=SNRGridAlphaBeta(
                    v_wall=form.cleaned_data["v_wall"],
                    T_star=form.cleaned_data["T_star"],
                    g_star=form.cleaned_data["g_star"],
                    alpha_points=alphas,
                    beta_over_H_points=beta_over_Hs,
                    v_wall_points=form.cleaned_data["v_wall"],
                    labels_points=label_list_final,
                    mission_profile=form.mission_profile,
                    engine=form.cleaned_data["engine"]
                )
            )
            return fig_to_response(fig)
    # Form not valid or not filled out
    return render(request, "multiple.html", {"form": MultipleForm()})


def parameter_choice_form(request: HttpRequest) -> HttpResponse:
    model = get_object_or_404_related(Model, prefetch=["points"], id=1)
    form = ParameterChoiceForm()
    context = {
        "model": model.name,
        "form": form,
    }
    return render(request, "parameterchoice.html", context)


def single(request: HttpRequest) -> HttpResponse:
    """Plot a single case - both query form and results"""
    if request.method == "GET":
        form = PTPlotForm(request.GET if request.GET else None)
        querystring = request.GET.urlencode()
    elif request.method == "POST":
        form = PTPlotForm(request.POST if request.POST else None)
        querystring = request.POST.urlencode()
    else:
        return render(request, "single.html", {"form": PTPlotForm()})

    if not form.is_valid():
        return render(request, "single.html", {"form": form})

    context = {
        "form": form,
        "querystring": querystring,
        "v_wall": form.cleaned_data["v_wall"],
        "alpha": form.cleaned_data["alpha"],
        "beta_over_H": form.cleaned_data["beta_over_H"],
        "T_star": form.cleaned_data["T_star"],
        "g_star": form.cleaned_data["g_star"],
        "mission_profile": form.mission_profile,
        "engine_name": ENGINE_NAMES[form.cleaned_data["engine"]],
        "css2": form.cleaned_data["css2"],
        "csb2": form.cleaned_data["csb2"]
    }
    return render(request, "single_result.html", context)
