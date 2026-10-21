"""PTPlot forms."""

import logging
import typing as tp

from django.core.exceptions import ValidationError
from django.db.models import QuerySet
from django.forms import CharField, FloatField, Form, IntegerField, Textarea
import numpy as np
from pttools.models import Model as EoSModel
from pttools.ssm.const import DEFAULT_N_T, DEFAULT_N_Z_LOOKUP

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
from ptplot.science import const
from ptplot.science.const import DEFAULT_LEGACY_NUCLEATION_CS_MAX
from ptplot.science.noise import DEFAULT_NOISE_EB, DEFAULT_NOISE_GB, DEFAULT_OBS_YEARS, Noise, noise_curve
from ptplot.science.snr.grid import GridAxes
from ptplot.science.spectrum.create import ssm_model
from ptplot.science.spectrum.engine import Engine
from ptplot.science.spectrum.ssm import BAG, SSMSettings

logger: logging.Logger = logging.getLogger(__name__)

#: Minimum values of the accuracy settings in :py:class:`SSMSettingsForm`,
#: which are those used for compiling the Numba functions in the dataset example of PTtools
MIN_N_Z_LOOKUP: int = 200
MIN_N_T: int = 100
MIN_NX_P_TILDE_GW: int = 50


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

    def __init__(self, data: tp.Mapping[str, tp.Any] | None = None, **kwargs: tp.Any):
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
    #: Equation of state model, set by :py:meth:`clean`
    _model: EoSModel = BAG
    # usetex = forms.BooleanField(
    #     label="Use TeX for labels (slow)?",
    #      initial=False,
    #      required=False
    # )

    @property
    def model(self) -> EoSModel:
        """Equation of state model of the SSM engine, or the bag model for the other engines.

        See :py:func:`ptplot.science.spectrum.create.ssm_model`.
        """
        return self._model

    def clean(self) -> dict[str, tp.Any]:
        r"""Validate that the equation of state model of the SSM can be created with the sound speeds.

        Also validate that $\alpha$ is within the valid range of the model.

        :return: Cleaned data
        :raises ValidationError: If the engine is the SSM and the model cannot be created with the sound speeds,
            or $\alpha$ is outside the valid range of the model
        """
        cleaned_data = tp.cast(dict[str, tp.Any], super().clean())
        self._model = BAG
        if cleaned_data.get("engine") == Engine.SSM:
            try:
                self._model = ssm_model(css2=cleaned_data.get("css2"), csb2=cleaned_data.get("csb2"))
            except ValueError as exc:
                raise ValidationError(f"Invalid sound speeds for the Sound Shell Model: {exc}") from exc
            alpha = cleaned_data.get("alpha")
            if alpha is not None and not self._model.alpha_n_min <= alpha <= self._model.alpha_n_max:
                raise ValidationError(
                    f"Invalid alpha={alpha} for the Sound Shell Model with these sound speeds. "
                    f"Valid range: {self._model.alpha_n_min:.4g} <= alpha <= {self._model.alpha_n_max:.4g}"
                )
        return cleaned_data


class GridAxesForm(Form):
    """Form for the size and limits of the axes of the SNR grids, given as optional query parameters.

    This is separate from the other forms so that these fields are not shown on the pages of the forms.
    The size cannot exceed :py:data:`ptplot.science.const.DEFAULT_GRID_SIZE`
    so that the query parameters cannot be used to request heavier computations than the default ones.
    The limits that are not given are deduced from the points and the default ranges,
    see :py:class:`ptplot.science.snr.grid.GridAxes`.
    """

    #: Names of the axes and their default ranges, see :py:class:`ptplot.science.snr.grid.GridAxes`
    AXES: tp.ClassVar[dict[str, tuple[str, np.ndarray]]] = {
        "alpha": ("alpha_n", const.DEFAULT_ALPHA_N_RANGE),
        "beta_tilde": ("beta_tilde", const.DEFAULT_beta_tilde_RANGE),
        "ubarf": ("ubarf", const.DEFAULT_UBARF_RANGE),
        "r_star": ("r_star", const.DEFAULT_R_STAR_RANGE),
    }

    grid_size = IntegerField(required=False, min_value=2, max_value=const.DEFAULT_GRID_SIZE)
    alpha_min = FloatField(required=False, min_value=0)
    alpha_max = FloatField(required=False, min_value=0)
    beta_tilde_min = FloatField(required=False, min_value=0)
    beta_tilde_max = FloatField(required=False, min_value=0)
    ubarf_min = FloatField(required=False, min_value=0)
    ubarf_max = FloatField(required=False, min_value=0)
    r_star_min = FloatField(required=False, min_value=0)
    r_star_max = FloatField(required=False, min_value=0)

    @property
    def axes(self) -> GridAxes:
        """Size and limits of the axes of the SNR grids."""
        size = self.cleaned_data["grid_size"]
        return GridAxes(
            size=const.DEFAULT_GRID_SIZE if size is None else size,
            **{
                f"{name}_{end}": self.cleaned_data[f"{field}_{end}"]
                for field, (name, _) in self.AXES.items()
                for end in ("min", "max")
            }
        )

    def clean(self) -> dict[str, tp.Any]:
        """Validate that the ranges of the axes are positive and increasing.

        A limit that is given alone is compared to the default range,
        as the other limit is at least as far from the given one as that of the default range.

        :return: Cleaned data
        :raises ValidationError: If a range would not be positive and increasing
        """
        cleaned_data = tp.cast(dict[str, tp.Any], super().clean())
        for field, (_, default) in self.AXES.items():
            range_min = cleaned_data.get(f"{field}_min")
            range_max = cleaned_data.get(f"{field}_max")
            if range_min is not None and range_min <= 0:
                raise ValidationError(f"{field}_min must be positive. Got: {range_min}")
            start = default[0] if range_min is None else range_min
            stop = default[-1] if range_max is None else range_max
            if not start < stop:
                raise ValidationError(
                    f"The range of {field} must be increasing. Got: {field}_min={range_min}, {field}_max={range_max}, "
                    f"default range: {default[0]:.4g} - {default[-1]:.4g}"
                )
        return cleaned_data


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

    underlying_model: ModelField
    v_wall: VWallField
    alpha: AlphaField
    beta_tilde: BetaTildeField

    def __init__(self) -> None:
        super().__init__()
        self.models: QuerySet[Model] = Model.objects.all()

        for _model in self.models:
            # Why is this defined within the loop?
            self.underlying_model = ModelField(self.models)

            # self.precomputed_choices = [
            #     (i, r"$g_\star = %g$, $T_n = %g\, \mathrm{GeV}$" % (gstar,Tn))
            #     for i, (gstar, Tn) in enumerate(zip(precomputed_gstar, precomputed_Tn))
            # ]

            self.v_wall = VWallField()
            # tstar = TStarField()
            self.alpha = AlphaField()
            self.beta_tilde = BetaTildeField()


class SSMSettingsForm(Form):
    """Form for the accuracy settings of the PTtools spectra of the SSM engine, given as optional query parameters.

    This is separate from the other forms so that these fields are not shown on the pages of the forms.
    The settings cannot exceed their defaults so that the query parameters cannot be used to request
    heavier computations than the default ones.
    See :py:class:`ptplot.science.spectrum.ssm.SSMSettings`.
    """

    n_z_lookup = IntegerField(required=False, min_value=MIN_N_Z_LOOKUP, max_value=DEFAULT_N_Z_LOOKUP)
    n_t = IntegerField(required=False, min_value=MIN_N_T, max_value=DEFAULT_N_T)
    nx_p_tilde_gw = IntegerField(required=False, min_value=MIN_NX_P_TILDE_GW, max_value=DEFAULT_N_Z_LOOKUP)

    @property
    def settings(self) -> SSMSettings:
        """Accuracy settings of the PTtools spectra, with the defaults for the settings that were not given."""
        return SSMSettings(**{
            name: value for name, value in self.cleaned_data.items() if value is not None
        })
