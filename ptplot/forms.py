import logging
import sys

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from ptplot.models import *
from ptplot.science.precomputed import AVAILABLE_LABELS

logger = logging.getLogger(__name__)


def validate_velocity(value: float) -> None:
    if not ((value > 0.0) and (value <= 1.0)):
        raise ValidationError(
            _("%(value)s must be greater than zero and less than or equal to 1"),
            params={"value": value},
        )


class PTPlotForm(forms.Form):
    available_MissionProfiles = [(i, label) for i, label in enumerate(AVAILABLE_LABELS)]

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
    BetaoverH = forms.FloatField(
        label=r"Inverse phase transition duration $\beta/H_*$",
        min_value=0.0,
        localize=False
    )
    Tstar = forms.FloatField(
        label=r"Transition temperature $T_\star$",
        min_value=0.0,
        localize=False
    )
    gstar = forms.FloatField(
        label=r"Degrees of freedom $g_\star$",
        min_value=0.0,
        localize=False
    )
    MissionProfile = forms.ChoiceField(
        label=r"Mission profile",
        choices=available_MissionProfiles
    )
   # usetex = forms.BooleanField(label="Use TeX for labels (slow)?",
   #                             initial=False,
   #                             required=False)

    def __init__(self, data=None, *args, **kwargs):
        super().__init__(data, *args, **kwargs)


class MultipleForm(forms.Form):
    available_MissionProfiles = [(i, label) for i, label in enumerate(AVAILABLE_LABELS)]

    vw = forms.FloatField(
        label=r"Wall velocity $v_\mathrm{w}$",
        min_value=0.0, max_value=1.0,
        validators=[validate_velocity],
        localize=False
    )
    Tstar = forms.FloatField(
        label=r"Transition temperature $T_\star$",
        min_value=0.0,
        localize=False
    )
    gstar = forms.FloatField(
        label=r"Degrees of freedom $g_\star$",
        min_value=0.0,
        localize=False
    )
    MissionProfile = forms.ChoiceField(
        label="Mission profile",
        choices=available_MissionProfiles
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
            print(model.model_name, file=sys.stderr)

            self.underlying_model = forms.ChoiceField(
                label=r"Model",
                choices=[(model.id, model.model_name) for model in self.models]
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
            self.BetaoverH = forms.FloatField(
                label=r"Inverse phase transition duration $\beta/H_*$",
                min_value=0.0,
                localize=False
            )
            self.MissionProfile = forms.ChoiceField(
                label="MissionProfile",
                choices=AVAILABLE_LABELS
            )
