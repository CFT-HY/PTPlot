import typing as tp

from django import forms
from django.db.models import QuerySet
from django.core.exceptions import ValidationError

from ptplot.models import Model
from ptplot.science.mission_profile import MISSION_PROFILE_CHOICES


def validate_velocity(value: float) -> None:
    if not (0 < value <= 1):
        raise ValidationError(f"{value} must be 0 < value <= 1")


class AlphaField(forms.FloatField):
    def __init__(
            self,
            label: str = r"Phase transition strength $\alpha_\theta$",
            min_value: float = 0.,
            **kwargs):
        super().__init__(label=label, min_value=min_value, **kwargs)


class BetaOverHField(forms.FloatField):
    def __init__(
            self,
            label: str = r"Inverse phase transition duration $\beta/H_*$",
            min_value: float = 0.,
            **kwargs):
        super().__init__(label=label, min_value=min_value, **kwargs)


class GStarField(forms.FloatField):
    def __init__(
            self,
            label: str = r"Degrees of freedom $g_\star$",
            min_value: float = 0.,
            **kwargs):
        super().__init__(label=label, min_value=min_value, **kwargs)


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
            **kwargs):
        super().__init__(label=label, min_value=min_value, **kwargs)


class VWField(forms.FloatField):
    def __init__(
            self,
            label: str = r"Wall velocity $v_\mathrm{w}$",
            min_value: float = 0.,
            max_value: float = 1.,
            validators: tp.Sequence[tp.Callable] = (validate_velocity, ),
            **kwargs):
        super().__init__(
            label=label,
            min_value=min_value, max_value=max_value,
            validators=validators,
            **kwargs
        )
