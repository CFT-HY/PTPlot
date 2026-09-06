"""Form fields."""

from fractions import Fraction
import typing as tp

from django import forms
from django.core.exceptions import ValidationError
from django.db.models import QuerySet
from django.forms.renderers import BaseRenderer
from django.utils.safestring import SafeString

from ptplot.models import Model
from ptplot.science.mission_profile import MISSION_PROFILE_CHOICES
from ptplot.science.spectrum.engine import ENGINE_CHOICES


def validate_velocity(value: float) -> None:
    """Validate that a velocity is within the range (0, 1]."""
    if not 0 < value <= 1:
        raise ValidationError(f"{value} must be 0 < value <= 1")


# -----
# Base field classes
# -----

class FractionField(forms.CharField):
    """Field that accepts both floats and fractions."""

    def to_python(self, value: str) -> float | Fraction | None:  # type: ignore
        if not value:
            return None
        try:
            return Fraction(value) if "/" in value else float(value)
        except (TypeError, ValueError) as err:
            raise ValidationError("Enter a float or a fraction.") from err


class UnitInput(forms.NumberInput):
    """NumberInput with units."""

    def __init__(self, attrs=None, units: str | None = None):
        super().__init__(attrs)
        self.units_string = None if units is None else SafeString(f"&nbsp;{units}")

    def render(
            self,
            name: str,
            value: tp.Any,
            attrs: dict[str, tp.Any] | None = None,
            renderer: BaseRenderer | None = None):
        ret = super().render(name, value, attrs, renderer)
        if self.units_string is None:
            return ret
        return ret + self.units_string


# -----
# Field classes for specific parameters
# -----

#: Default widget of the transition temperature field
GEV_INPUT = UnitInput(units="GeV")

# Disabling localization for FloatField enables the use of NumberInput
# https://docs.djangoproject.com/en/5.2/ref/forms/fields/#floatfield

class AlphaField(forms.FloatField):
    r"""Field for the phase transition strength $\alpha_\theta$."""

    def __init__(
            self,
            label: str = r"Phase transition strength $\alpha_\theta$",
            min_value: float = 0.,
            localize: bool = False,
            **kwargs):
        super().__init__(label=label, min_value=min_value, localize=localize, **kwargs)


class BetaOverHField(forms.FloatField):
    r"""Field for the inverse phase transition duration $\frac{\beta}{H_*}$."""

    def __init__(
            self,
            label: str = r"Inverse phase transition duration $\beta/H_*$",
            min_value: float = 0.,
            localize: bool = False,
            **kwargs):
        super().__init__(label=label, min_value=min_value, localize=localize, **kwargs)


class CS2Field(FractionField):
    r"""Field for the sound speed squared $c_s^2$."""

    def __init__(
            self,
            label: str = r"Sound speed squared $c_s^2$",
            help_text: str = "Sound Shell Model only",
            # min_value: float = 0.,
            # max_value: float = 1.,
            validators: tp.Sequence[tp.Callable] = (validate_velocity, ),
            **kwargs):
        super().__init__(
            label=label, help_text=help_text,
            # min_value=min_value, max_value=max_value,
            validators=validators,
            **kwargs
        )


class CSS2Field(CS2Field):
    r"""Field for the sound speed squared in the symmetric phase $c_{s,s}^2$."""

    def __init__(
            self,
            label: str = r"Sound speed squared in the symmetric phase $c_{s,s}^2$",
            **kwargs):
        super().__init__(label=label, **kwargs)


class CSB2Field(CS2Field):
    r"""Field for the sound speed squared in the broken phase $c_{s,b}^2$."""

    def __init__(
            self,
            label: str = r"Sound speed squared in the broken phase $c_{s,b}^2$",
            **kwargs):
        super().__init__(label=label, **kwargs)


class EngineField(forms.ChoiceField):
    """Field for choosing the power spectrum engine."""

    def __init__(
            self,
            label: str = "Engine",
            choices=ENGINE_CHOICES,
            **kwargs):
        super().__init__(label=label, choices=choices, **kwargs)


class GStarField(forms.FloatField):
    r"""Field for the degrees of freedom $g_*$."""

    def __init__(
            self,
            label: str = r"Degrees of freedom $g_\star$",
            min_value: float = 0.,
            localize: bool = False,
            **kwargs):
        super().__init__(label=label, min_value=min_value, localize=localize, **kwargs)


class MissionProfileField(forms.TypedChoiceField):
    """Field for choosing the mission profile."""

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

    # def to_python(self, value) -> MissionProfile | None:
    #     if value is None or value == "":
    #         return None
    #     converted = int(super().to_python(value))
    #     return MissionProfile.from_ind(converted)


class ModelField(forms.ModelChoiceField):
    """Field for choosing the model."""

    def __init__(
            self,
            queryset: QuerySet | None = None,
            label: str = "Model",
            **kwargs):
        super().__init__(
            queryset=Model.objects.all() if queryset is None else queryset,
            label=label,
            **kwargs
        )


class TStarField(forms.FloatField):
    r"""Field for the transition temperature $T_*$."""

    def __init__(
            self,
            label: str = r"Transition temperature $T_\star$",
            min_value: float = 0.,
            widget: forms.NumberInput = GEV_INPUT,
            localize: bool = False,
            **kwargs):
        super().__init__(
            label=label, min_value=min_value, widget=widget, localize=localize,
            **kwargs
        )


class VWallField(forms.FloatField):
    r"""Field for the wall velocity $v_\text{wall}$."""

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
