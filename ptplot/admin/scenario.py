"""Scenario admin"""

from django.contrib import admin

from ptplot import models
from ptplot.admin.base import CustomModelAdmin, admin_site
import ptplot.methods.admin as admin_methods


@admin.register(models.Scenario, site=admin_site)
class ScenarioAdmin(CustomModelAdmin):
    list_display = [
        "name", "model_link", "number", "T_star", "description"
    ]
    list_filter = ["T_star"]
    list_select_related = ["model"]
    search_fields = ["name", "model__name", "T_star", "description"]
    autocomplete_fields = ["model"]

    model_link = admin_methods.generate_link("model")
