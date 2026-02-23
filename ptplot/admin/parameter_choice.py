from django.contrib import admin

from ptplot import models
from ptplot.admin.base import CustomModelAdmin, admin_site
import ptplot.methods.admin as admin_methods


@admin.register(models.ParameterChoice, site=admin_site)
class ParameterChoiceAdmin(CustomModelAdmin):
    list_display = [
        "long_label", "model_link", "number", "scenario_link",
        "v_wall", "alpha", "beta_over_H", "T_star", "g_star"
    ]
    list_filter = ["g_star"]
    list_select_related = ["model", "scenario"]
    search_fields = [
        "long_label", "short_label",
        "model__name", "scenario__name",
        "alpha", "beta_over_H", "T_star", "g_star"
    ]
    autocomplete_fields = ["model", "scenario"]

    model_link = admin_methods.generate_link("model")
    scenario_link = admin_methods.generate_link("scenario")
