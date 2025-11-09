from django.contrib import admin


class PTPlotAdminSite(admin.AdminSite):
    site_header = "PTPlot administration"
    login_template = "github_sso/login.html"


class CustomModelAdmin(admin.ModelAdmin):
    pass


admin_site = PTPlotAdminSite(name="ptplot-admin")
