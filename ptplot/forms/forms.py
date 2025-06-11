import logging

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from ptplot.forms.fields import MissionProfileField
from ptplot.models import Model
from ptplot.science.mission_profile import MissionProfile

logger = logging.getLogger(__name__)


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
    mission_profile_ind = MissionProfileField()
    # engine = forms.ChoiceField()
    # usetex = forms.BooleanField(
    #     label="Use TeX for labels (slow)?",
    #      initial=False,
    #      required=False
    # )

    def __init__(self, data=None, *args, **kwargs):
        super().__init__(data, *args, **kwargs)

    @property
    def mission_profile(self) -> MissionProfile:
        return MissionProfile.from_ind(self.cleaned_data["mission_profile_ind"])


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
    mission_profile_ind = MissionProfileField()
    table = forms.CharField(
        label="Input table",
        widget=forms.Textarea,
        initial="#alpha_theta,BetaOverH,label"
    )

    @property
    def mission_profile(self) -> MissionProfile:
        return MissionProfile.from_ind(self.cleaned_data["mission_profile"])


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
            self.underlying_model = forms.TypedChoiceField(
                label=r"Model",
                choices=[(model.id, model.name) for model in self.models],
                coerce=int,
                empty_value=None
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
            self.mission_profile = MissionProfileField()
