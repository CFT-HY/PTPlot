import logging

from ptplot.forms.fields import *
from ptplot.models import Model
from ptplot.science.mission_profile import MissionProfile

logger = logging.getLogger(__name__)


class PTPlotForm(forms.Form):
    vw = VWField()
    alpha = AlphaField()
    beta_over_H = BetaOverHField()
    T_star = TStarField()
    g_star = GStarField()
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
    vw = VWField()
    T_star = TStarField()
    g_star = GStarField()
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
        self.models = Model.objects.all()

        for model in self.models:
            # Why is this defined within the loop?
            self.underlying_model = ModelField(self.models)

            # self.precomputed_choices = [(i, r"$g_\star = %g$, $T_n = %g\, \mathrm{GeV}$" % (gstar,Tn)) for i, (gstar, Tn) in enumerate(zip(precomputed_gstar, precomputed_Tn))]

            self.vw = VWField
            # tstar = TStarField()
            self.alpha = AlphaField()
            self.beta_over_H = BetaOverHField()
            self.mission_profile = MissionProfileField()
