"""Validation of the query parameters of the views."""

from dataclasses import dataclass

from django.forms import Form
from django.http import HttpRequest, HttpResponseBadRequest

from ptplot.forms import GridAxesForm, SSMSettingsForm
from ptplot.science.snr.grid import GridAxes
from ptplot.science.spectrum.ssm import SSMSettings


@dataclass(frozen=True, slots=True)
class ValidatedForms[F: Form]:
    """The validated form of a view, and the settings given in the query parameters."""

    #: The validated form of the view
    form: F
    #: Size and limits of the axes of the SNR grids, see :py:class:`ptplot.forms.GridAxesForm`
    axes: GridAxes
    #: Accuracy settings of the SSM, see :py:class:`ptplot.forms.SSMSettingsForm`
    ssm_settings: SSMSettings


def validate_forms[F: Form](request: HttpRequest, form_class: type[F]) -> ValidatedForms[F] | HttpResponseBadRequest:
    """Create and validate the form of a view, and the forms of the optional settings, from the query parameters.

    The optional settings are those of :py:class:`ptplot.forms.GridAxesForm` and
    :py:class:`ptplot.forms.SSMSettingsForm`, which are validated for all the views,
    even though only some of the views use them.

    :param request: HTTP request
    :param form_class: Class of the form of the view
    :return: The validated forms,
        or a response with the errors as plain text if any of the forms is invalid.
        The errors are not returned as HTML, as they can contain the given values.
    """
    form = form_class(request.GET)
    axes_form = GridAxesForm(request.GET)
    settings_form = SSMSettingsForm(request.GET)
    errors = [f.errors.as_text() for f in (form, axes_form, settings_form) if not f.is_valid()]
    if errors:
        return HttpResponseBadRequest(
            "Invalid query parameters:\n" + "\n".join(errors),
            content_type="text/plain; charset=utf-8"
        )
    return ValidatedForms(form=form, axes=axes_form.axes, ssm_settings=settings_form.settings)
