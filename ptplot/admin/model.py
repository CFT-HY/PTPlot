from django.contrib import admin

from ptplot import models
from ptplot.admin.base import CustomModelAdmin, admin_site


@admin.register(models.Model, site=admin_site)
class ModelAdmin(CustomModelAdmin):
    list_display = [
        "name", "vw", "T_star", "g_star",
        "huge_alpha", "has_scenarios"
    ]
    list_filter = [
        "vw", "T_star", "g_star",
        "huge_alpha", "has_scenarios"
    ]
    search_fields = [
        "name", "description", "notes",
        "vw", "T_star", "g_star",
        "huge_alpha", "has_scenarios"
    ]
