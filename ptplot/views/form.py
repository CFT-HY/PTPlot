from ptplot.forms import MultipleForm, ParameterChoiceForm, PTPlotForm
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from ptplot.methods import fig_to_response, get_object_or_404_related
from ptplot.models import Model
from ptplot.science.engine import ENGINE_NAMES
from ptplot.science.snr_alphabeta_onthefly import get_snr_alphabeta_image


def multiple(request: HttpRequest) -> HttpResponse:
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

            fig = get_snr_alphabeta_image(
                vw=form.cleaned_data["vw"],
                alphas=alphas,
                beta_over_Hs=beta_over_Hs,
                T_star=form.cleaned_data["T_star"],
                g_star=form.cleaned_data["g_star"],
                mission_profile=form.mission_profile,
                labels=label_list_final,
                engine=form.cleaned_data["engine"]
            )
            return fig_to_response(fig)
    # Form not valid or not filled out
    return render(request, "multiple.html", {"form": MultipleForm()})


def parameterchoice_form(request: HttpRequest) -> HttpResponse:
    model = get_object_or_404_related(Model, prefetch=["points"], id=1)
    form = ParameterChoiceForm()
    context = {
        "model": model.name,
        "form": form,
    }
    return render(request, "parameterchoice.html", context)


def single(request: HttpRequest) -> HttpResponse:
    querystring = request.GET.urlencode()

    # If this is a POST request we need to process the form data
    if request.method == "GET" and querystring:
        form = PTPlotForm(request.GET)

        if form.is_valid():
            context = {
                "form": form,
                "querystring": querystring,
                "vw": form.cleaned_data["vw"],
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

        # Form not valid
        return render(request, "single.html", {"form": form})

    # No form yet
    return render(request, "single.html", {"form": PTPlotForm()})
