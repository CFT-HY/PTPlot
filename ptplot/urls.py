"""Django URL configuration"""

from django.urls import URLPattern, path, re_path
from django.views.generic import RedirectView

from . import views


urlpatterns: list[URLPattern] = [
    # -----
    # Plots and CSV from query parameters
    # -----
    path("curvedata.csv", views.csv, name="csv"),
    path("ps.svg", views.ps_image, name="ps"),
    path("snr_alpha_beta.svg", views.snr_alpha_beta, name="snr_alpha_beta"),
    path("snr_ubarf_rstar.svg", views.snr_ubarf_rstar, name="snr_ubarf_rstar"),

    # -----
    # Single point
    # -----
    path("single", views.single, name="single"),

    # -----
    # Multiple points
    # -----
    path("multiple", views.multiple, name="multiple"),
    path("multiple.svg", views.multiple, name="multiple"),

    # -----
    # Model
    # -----
    path("models", views.models, name="models"),
    path("models/<int:model_id>", views.model_detail, name="model_detail"),
    path("models/<int:model_id>/plot", views.model_detail_plot, name="model_detail_plot"),
    path("models/<int:model_id>/snr_alpha_beta.svg", views.model_snr_alpha_beta, name="model_snr_alpha_beta"),
    path("models/<int:model_id>/snr_histogram.svg", views.model_snr_histogram, name="model_snr_histogram"),
    path("models/<int:model_id>/snr_ubarf_rstar.svg", views.model_snr_ubarf_rstar, name="model_snr_ubarf_rstar"),

    # -----
    # Point
    # -----
    path("models/<int:model_id>/<int:point_id>/plot", views.model_point_plot, name="model_point_plot"),
    # Download CSV data for an individual model point
    path(
        "models/<int:model_id>/<int:point_id>/curvedata.csv",
        views.model_point_csv,
        name="model_point_csv"
    ),
    path(
        "models/<int:model_id>/<int:point_id>/ps.svg",
        views.model_point_ps,
        name="model_point_ps"
    ),
    path(
        "models/<int:model_id>/<int:point_id>/snr_alpha_beta.svg",
        views.model_point_snr_alpha_beta,
        name="model_point_snr_alpha_beta"
    ),
    path(
        "models/<int:model_id>/<int:point_id>/snr_ubarf_rstar.svg",
        views.model_point_snr_ubarf_rstar,
        name="model_point_snr_ubarf_rstar"
    ),

    # -----
    # Scenario
    # -----
    path(
        "models/<int:model_id>/scenarios/<int:scenario_id>/plot",
        views.model_scenario_plot,
        name="model_scenario_plot"
    ),
    path(
        "models/<int:model_id>/scenarios/<int:scenario_id>/snr_alpha_beta.svg",
        views.model_scenario_snr_alpha_beta,
        name="model_scenario_snr_alpha_beta"
    ),
    path(
        "models/<int:model_id>/scenarios/<int:scenario_id>/snr_histogram.svg",
        views.model_scenario_snr_histogram,
        name="model_scenario_snr_histogram"
    ),
    path(
        "models/<int:model_id>/scenarios/<int:scenario_id>/snr_ubarf_rstar.svg",
        views.model_scenario_snr_ubarf_rstar,
        name="model_scenario_snr_ubarf_rstar"
    ),

    # -----
    # Parameter choice
    # -----
    path("parameter_choice", views.parameter_choice_form, name="parameter_choice"),

    # -----
    # Handle legacy URLs with redirects
    # -----
    # Old name for models
    re_path("theories*", RedirectView.as_view(url="/ptplot/models", permanent=True)),
    # Old paths for plots didn't have the file extensions
    re_path(
        r"^(?P<anything>.*)ps$",
        RedirectView.as_view(
            url="/ptplot/%(anything)sps.svg",
            permanent=True,
            query_string=True
        )
    ),
    re_path(
        r"^(?P<anything>.*)snr(?:\.svg)?$",
        RedirectView.as_view(
            url="/ptplot/%(anything)ssnr_ubarf_rstar.svg",
            permanent=True,
            query_string=True
        )
    ),
    re_path(
        r"^(?P<anything>.*)snr_alphabeta(?:\.svg)?$",
        RedirectView.as_view(
            url="/ptplot/%(anything)ssnr_alpha_beta.svg",
            permanent=True,
            query_string=True
        )
    ),

    # -----
    # Index page
    # -----
    # This must be the last, since otherwise "" would match all other URLs.
    path("", views.index, name="index"),
]
