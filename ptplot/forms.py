import logging
# import sys
import typing as tp

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from ptplot.models import *
from ptplot.science.precomputed import AVAILABLE_LABELS

logger = logging.getLogger(__name__)
MISSION_PROFILES: tp.List[tp.Tuple[int, str]] = [(i, label) for i, label in enumerate(AVAILABLE_LABELS)]


def validate_velocity(value: float) -> None:
    if not ((value > 0.0) and (value <= 1.0)):
        raise ValidationError(
            _("%(value)s must be greater than zero and less than or equal to 1"),
            params={"value": value},
        )


class PTPlotForm(forms.Form):
    vw = forms.FloatField(
        label=r"Wall velocity $v_\mathrm{w}$",
        min_value=0.0, max_value=1.0,
        validators=[validate_velocity],
        localize=False
    )
    alpha = forms.FloatField(
        label=r"Phase transition strength $\alpha_\theta$",
        min_value=0.0,
        localize=False
    )
    beta_over_H = forms.FloatField(
        label=r"Inverse phase transition duration $\beta/H_*$",
        min_value=0.0,
        localize=False
    )
    T_star = forms.FloatField(
        label=r"Transition temperature $T_\star$",
        min_value=0.0,
        localize=False
    )
    g_star = forms.FloatField(
        label=r"Degrees of freedom $g_\star$",
        min_value=0.0,
        localize=False
    )
    mission_profile = forms.ChoiceField(
        label=r"Mission profile",
        choices=MISSION_PROFILES
    )
   # usetex = forms.BooleanField(
   #     label="Use TeX for labels (slow)?",
   #      initial=False,
   #      required=False
   # )

    def __init__(self, data=None, *args, **kwargs):
        super().__init__(data, *args, **kwargs)


class MultipleForm(forms.Form):
    vw = forms.FloatField(
        label=r"Wall velocity $v_\mathrm{w}$",
        min_value=0.0, max_value=1.0,
        validators=[validate_velocity],
        localize=False
    )
    T_star = forms.FloatField(
        label=r"Transition temperature $T_\star$",
        min_value=0.0,
        localize=False
    )
    g_star = forms.FloatField(
        label=r"Degrees of freedom $g_\star$",
        min_value=0.0,
        localize=False
    )
    mission_profile = forms.ChoiceField(
        label="Mission profile",
        choices=MISSION_PROFILES
    )
    table = forms.CharField(
        label="Input table",
        widget=forms.Textarea,
        initial="#alpha_theta,BetaOverH,label"
    )


class ParameterChoiceForm(forms.Form):
    def __init__(self):
        super().__init__()
        self.models = []

        try:
            self.models = Model.objects.all()
        except Exception as e:
            logger.exception("Error retrieving models", exc_info=e)

        for model in self.models:
            # print(model.name, file=sys.stderr)
            self.underlying_model = forms.ChoiceField(
                label=r"Model",
                choices=[(model.id, model.name) for model in self.models]
            )

            # self.precomputed_choices = [(i, r"$g_\star = %g$, $T_n = %g\, \mathrm{GeV}$" % (gstar,Tn)) for i, (gstar, Tn) in enumerate(zip(precomputed_gstar, precomputed_Tn))]

            self.vw = forms.FloatField(
                label=r"Wall velocity $v_\mathrm{w}$",
                min_value=0.0,
                max_value=1.0,
                validators=[validate_velocity],
                localize=False
            )
            # tstar = forms.FloatField(
            #     label=r"Phase transition temperature $T_*$",
            #     min_value=0.0
            # )
            self.alpha = forms.FloatField(
                label=r"Phase transition strength $\alpha_\theta$",
                min_value=0.0,
                localize=False
            )
            self.beta_over_H = forms.FloatField(
                label=r"Inverse phase transition duration $\beta/H_*$",
                min_value=0.0,
                localize=False
            )
            self.mission_profile = forms.ChoiceField(
                label="MissionProfile",
                choices=AVAILABLE_LABELS
            )
