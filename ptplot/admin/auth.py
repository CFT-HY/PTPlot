"""Authentication admin."""

import typing as tp

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.models import AbstractUser
from django_github_sso.admin import GitHubSSOInlineAdmin, get_current_user_and_admin

from ptplot import models
from ptplot.admin.base import CustomModelAdmin, admin_site

_current_user_model, last_admin, LastUserAdmin = get_current_user_and_admin()
# get_current_user_and_admin() is annotated to return a user, but it returns the user model class.
CurrentUserModel = tp.cast("type[AbstractUser]", _current_user_model)

if admin.site.is_registered(CurrentUserModel):
    admin.site.unregister(CurrentUserModel)


@admin.register(models.User, site=admin_site)
class UserAdmin(CustomModelAdmin, DjangoUserAdmin):
    """Admin for users."""

    inlines = (
        tuple({*last_admin.inlines, GitHubSSOInlineAdmin})
        if last_admin
        else (GitHubSSOInlineAdmin,)
    )
