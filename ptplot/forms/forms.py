"""PTPlot forms"""

import logging
import typing as tp

from django.forms import CharField, Form, Textarea
from ptplot.forms.fields import \
    AlphaField, BetaOverHField, CSS2Field, CSB2Field, EngineField, \
    GStarField, MissionProfileField, ModelField, TStarField, VWallField
from ptplot.models import Model, ParameterChoice, Scenario
from ptplot.science.spectrum.engine import Engine
from ptplot.science.mission_profile import MissionProfile

logger = logging.getLogger(__name__)


class BenchmarkForm(Form):
    """Form for the arguments of the benchmark plots"""
    mission_profile_ind = MissionProfileField()
    engine = EngineField()

    def __init__(
            self,
            data: tp.Mapping[str, tp.Any] | None = None,
            model: Model | None = None,
            point: ParameterChoice | None = None,
            scenario: Scenario | None = None,
            **kwargs):
        if data is None or "mission_profile_ind" not in data:
            if point is not None:
                model = point.model
            elif scenario is not None:
                model = scenario.model

            if model is not None:
                data = {"mission_profile_ind": model.mission_profile_ind} \
                    if data is None else \
                    {**data, "mission_profile_ind": model.mission_profile_ind}
        if "engine" not in data:
            data["engine"] = Engine.DEFAULT

        super().__init__(data, **kwargs)

    @property
    def mission_profile(self) -> MissionProfile:
        """Get the mission profile object"""
        return MissionProfile.from_ind(self.cleaned_data["mission_profile_ind"])


class PTPlotForm(Form):
    """Form for the arguments of a single point"""
    v_wall = VWallField()
    alpha = AlphaField()
    beta_over_H = BetaOverHField()
    T_star = TStarField()
    g_star = GStarField()
    mission_profile_ind = MissionProfileField()
    css2 = CSS2Field(required=False)
    csb2 = CSB2Field(required=False)
    engine = EngineField()
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


class MultipleForm(Form):
    """Form for the arguments of multiple points"""
    vw = VWallField()
    T_star = TStarField()
    g_star = GStarField()
    mission_profile_ind = MissionProfileField()
    table = CharField(
        label="Input table",
        widget=Textarea,
        initial="#alpha_theta,BetaOverH,label"
    )

    @property
    def mission_profile(self) -> MissionProfile:
        return MissionProfile.from_ind(self.cleaned_data["mission_profile"])


class ParameterChoiceForm(Form):
    """Parameter choice form"""
    def __init__(self):
        super().__init__()
        self.models = Model.objects.all()

        for model in self.models:
            # Why is this defined within the loop?
            self.underlying_model = ModelField(self.models)

            # self.precomputed_choices = [
            #     (i, r"$g_\star = %g$, $T_n = %g\, \mathrm{GeV}$" % (gstar,Tn))
            #     for i, (gstar, Tn) in enumerate(zip(precomputed_gstar, precomputed_Tn))
            # ]

            self.v_wall = VWallField
            # tstar = TStarField()
            self.alpha = AlphaField()
            self.beta_over_H = BetaOverHField()
            self.mission_profile = MissionProfileField()
