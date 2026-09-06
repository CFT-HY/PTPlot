"""Base admins."""

from django.contrib import admin


class PTPlotAdminSite(admin.AdminSite):
    """PTPlot admin site."""

    site_header = "PTPlot administration"
    login_template = "github_sso/login.html"


class CustomModelAdmin(admin.ModelAdmin):
    """Custom base class for model admins."""


admin_site = PTPlotAdminSite(name="ptplot-admin")
