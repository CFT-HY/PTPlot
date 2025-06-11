import typing as tp

from django import forms
from django.db.models import QuerySet
from django.core.exceptions import ValidationError
from django.forms.renderers import BaseRenderer
from django.utils.safestring import SafeString

from ptplot.models import Model
from ptplot.science.mission_profile import MISSION_PROFILE_CHOICES


def validate_velocity(value: float) -> None:
    if not (0 < value <= 1):
        raise ValidationError(f"{value} must be 0 < value <= 1")


# -----
# Base field classes
# -----

class UnitInput(forms.NumberInput):
    def __init__(self, attrs=None, units: str = None):
        super().__init__(attrs)
        self.units_string = None if units is None else SafeString(f"&nbsp;{units}")

    def render(
            self,
            name: str,
            value: tp.Any,
            attrs: dict[str, tp.Any] = None,
            renderer: BaseRenderer = None):
        ret = super().render(name, value, attrs, renderer)
        if self.units_string is None:
            return ret
        return ret + self.units_string


# -----
# Field classes for specific parameters
# -----

# Disabling localization for FloatField enables the use of NumberInput
# https://docs.djangoproject.com/en/5.2/ref/forms/fields/#floatfield

class AlphaField(forms.FloatField):
    def __init__(
            self,
            label: str = r"Phase transition strength $\alpha_\theta$",
            min_value: float = 0.,
            localize: bool = False,
            **kwargs):
        super().__init__(label=label, min_value=min_value, localize=localize, **kwargs)


class BetaOverHField(forms.FloatField):
    def __init__(
            self,
            label: str = r"Inverse phase transition duration $\beta/H_*$",
            min_value: float = 0.,
            localize: bool = False,
            **kwargs):
        super().__init__(label=label, min_value=min_value, localize=localize, **kwargs)



class GStarField(forms.FloatField):
    def __init__(
            self,
            label: str = r"Degrees of freedom $g_\star$",
            min_value: float = 0.,
            localize: bool = False,
            **kwargs):
        super().__init__(label=label, min_value=min_value, localize=localize, **kwargs)


class MissionProfileField(forms.TypedChoiceField):
    def __init__(
            self,
            label: str = r"Mission profile",
            choices=MISSION_PROFILE_CHOICES,
            coerce=int,
            empty_value=None,
            **kwargs):
        super().__init__(
            label=label, choices=choices, coerce=coerce,
            empty_value=empty_value, **kwargs
        )

    # def to_python(self, value) -> tp.Optional[MissionProfile]:
    #     if value is None or value == "":
    #         return None
    #     converted = int(super().to_python(value))
    #     return MissionProfile.from_ind(converted)


class ModelField(forms.ModelChoiceField):
    def __init__(
            self,
            queryset: QuerySet = None,
            label: str = "Model",
            **kwargs):
        super().__init__(
            queryset=Model.objects.all() if queryset is None else queryset,
            label=label,
            **kwargs
        )


class TStarField(forms.FloatField):
    def __init__(
            self,
            label: str = r"Transition temperature $T_\star$",
            min_value: float = 0.,
            widget: forms.NumberInput = UnitInput(units="GeV"),
            localize: bool = False,
            **kwargs):
        super().__init__(
            label=label, min_value=min_value, widget=widget, localize=localize,
            **kwargs
        )


class VWField(forms.FloatField):
    def __init__(
            self,
            label: str = r"Wall velocity $v_\mathrm{w}$",
            min_value: float = 0.,
            max_value: float = 1.,
            validators: tp.Sequence[tp.Callable] = (validate_velocity, ),
            localize: bool = False,
            **kwargs):
        super().__init__(
            label=label,
            min_value=min_value, max_value=max_value,
            validators=validators,
            localize=localize,
            **kwargs
        )
