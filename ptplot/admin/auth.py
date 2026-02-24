"""Authentication admin"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django_github_sso.admin import (
    GitHubSSOInlineAdmin, get_current_user_and_admin
)

from ptplot import models
from ptplot.admin.base import CustomModelAdmin, admin_site


CurrentUserModel, last_admin, LastUserAdmin = get_current_user_and_admin()

if admin.site.is_registered(CurrentUserModel):
    admin.site.unregister(CurrentUserModel)


@admin.register(models.User, site=admin_site)
class UserAdmin(CustomModelAdmin, DjangoUserAdmin):
    inlines = (
        tuple(set(list(last_admin.inlines) + [GitHubSSOInlineAdmin]))
        if last_admin
        else (GitHubSSOInlineAdmin,)
    )
