"""Methods for Django admin interface."""

import typing as tp

from django.contrib.admin import display as admin_display
from django.db import models
from django.urls import reverse
from django.utils.html import format_html


def admin_change_url(obj: models.Model):
    """Get the admin change URL of an object.

    Adapted from
    https://medium.com/@hakibenita/things-you-must-know-about-django-admin-as-your-app-gets-bigger-6be0b0ee9614
    """
    app_label = obj._meta.app_label  # noqa: SLF001
    model_name = obj._meta.model.__name__.lower()  # noqa: SLF001
    return reverse(f"admin:{app_label}_{model_name}_change", args=(obj.pk, ))


def generate_link(target: str, name: str | None = None) -> tp.Callable:
    """
    Create a link column to a related model.

    :param target: target field
    :param name: visible name of the field
    """
    if name is None:
        name = target

    @admin_display(description=name.replace("_", " "))
    def generated_link(obj: models.Model):
        target_obj = getattr(obj, target)
        return link(target_obj)

    return staticmethod(generated_link)


def link(obj: models.Model):
    """Create a link to the given object."""
    if obj is None:
        return ""
    url = obj.get_absolute_url() if hasattr(obj, "get_absolute_url") else admin_change_url(obj)
    return format_html(
        """<a href="{}">{}</a>""",
        url, obj
    )
