"""PTPlot forms."""

import logging
import typing as tp

from django.forms import CharField, Form, Textarea

from ptplot.forms.fields import (
    AlphaField,
    BetaTildeField,
    CSB2Field,
    CSS2Field,
    EngineField,
    GStarField,
    LegacyNucleationCsMaxField,
    ModelField,
    NoiseEBField,
    NoiseGBField,
    ObsYearsField,
    TStarField,
    VWallField,
)
from ptplot.models import Model
from ptplot.science.const import DEFAULT_LEGACY_NUCLEATION_CS_MAX
from ptplot.science.noise import DEFAULT_NOISE_EB, DEFAULT_NOISE_GB, DEFAULT_OBS_YEARS, Noise, noise_curve

logger = logging.getLogger(__name__)


class NoiseFormMixin(Form):
    """Mixin that adds the noise curve fields and the resulting noise curve."""

    obs_years = ObsYearsField()
    noise_eb = NoiseEBField()
    noise_gb = NoiseGBField()

    @property
    def noise(self) -> Noise:
        """Get the noise curve object."""
        return noise_curve(
            obs_years=self.cleaned_data["obs_years"],
            eb=self.cleaned_data["noise_eb"],
            gb=self.cleaned_data["noise_gb"]
        )


class NucleationFormMixin(Form):
    r"""Mixin that adds the choice of the $\tilde{\beta} \leftrightarrow r_*$ conversion."""

    legacy_nucleation_cs_max = LegacyNucleationCsMaxField()


class BenchmarkForm(NoiseFormMixin, NucleationFormMixin):
    """Form for the arguments of the benchmark plots."""

    engine = EngineField(required=False)
    field_order = ["obs_years", "noise_eb", "noise_gb", "legacy_nucleation_cs_max", "engine"]

    def __init__(self, data: tp.Mapping[str, tp.Any] | None = None, **kwargs):
        # dict(data.items()) instead of {**data}, since the latter would give the
        # underlying lists of values of a QueryDict instead of the values themselves.
        data = {} if not data else dict(data.items())
        if "obs_years" not in data:
            # The form has not been submitted, so the defaults are used.
            # The checkboxes have to be filled in explicitly,
            # since an unchecked checkbox is indistinguishable from a missing one.
            data["obs_years"] = DEFAULT_OBS_YEARS
            data.setdefault("noise_eb", DEFAULT_NOISE_EB)
            data.setdefault("noise_gb", DEFAULT_NOISE_GB)
            data.setdefault("legacy_nucleation_cs_max", DEFAULT_LEGACY_NUCLEATION_CS_MAX)
        # if "engine" not in data:
        #    data["engine"] = Engine.DEFAULT
        super().__init__(data, **kwargs)


class PTPlotForm(NoiseFormMixin, NucleationFormMixin):
    """Form for the arguments of a single point."""

    v_wall = VWallField()
    alpha = AlphaField()
    beta_tilde = BetaTildeField()
    T_star = TStarField()
    g_star = GStarField()
    css2 = CSS2Field(required=False)
    csb2 = CSB2Field(required=False)
    engine = EngineField()
    # Keep the noise and nucleation fields of the mixins after the parameters of the point.
    field_order = [
        "v_wall", "alpha", "beta_tilde", "T_star", "g_star", "css2", "csb2", "engine",
        "obs_years", "noise_eb", "noise_gb", "legacy_nucleation_cs_max"
    ]
    # usetex = forms.BooleanField(
    #     label="Use TeX for labels (slow)?",
    #      initial=False,
    #      required=False
    # )


class MultipleForm(NoiseFormMixin, NucleationFormMixin):
    """Form for the arguments of multiple points."""

    v_wall = VWallField()
    T_star = TStarField()
    g_star = GStarField()
    table = CharField(
        label="Input table",
        widget=Textarea,
        initial="#alpha_theta,BetaOverH,label"
    )
    engine = EngineField()
    # Keep the noise and nucleation fields of the mixins after the parameters of the points.
    field_order = [
        "v_wall", "T_star", "g_star", "table", "engine", "obs_years", "noise_eb", "noise_gb", "legacy_nucleation_cs_max"
    ]


class ParameterChoiceForm(Form):
    """Parameter choice form."""

    def __init__(self):
        super().__init__()
        self.models = Model.objects.all()

        for _model in self.models:
            # Why is this defined within the loop?
            self.underlying_model = ModelField(self.models)

            # self.precomputed_choices = [
            #     (i, r"$g_\star = %g$, $T_n = %g\, \mathrm{GeV}$" % (gstar,Tn))
            #     for i, (gstar, Tn) in enumerate(zip(precomputed_gstar, precomputed_Tn))
            # ]

            self.v_wall = VWallField
            # tstar = TStarField()
            self.alpha = AlphaField()
            self.beta_tilde = BetaTildeField()
