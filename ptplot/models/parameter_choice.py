"""Parameter choices for particle physics models"""

from django.core import validators
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from matplotlib.figure import Figure

from ptplot.models.model import Model
from ptplot.models.scenario import Scenario
from ptplot.science import const
from ptplot.science.mission_profile import MissionProfile
from ptplot.science.plot.power_spectrum import power_spectrum_figure
from ptplot.science.plot.snr_alpha_beta import snr_figure_alpha_beta
from ptplot.science.plot.snr_comparison import snr_comparison
from ptplot.science.plot.snr_ubarf_rstar import snr_figure_ubarf_rstar
from ptplot.science.spectrum import Engine, power_spectrum


class ParameterChoice(models.Model):
    """A parameter choice, aka. a point, for a particle physics model"""
    model = models.ForeignKey(Model, on_delete=models.CASCADE, related_name="points")
    number = models.IntegerField()
    short_label = models.CharField(max_length=2)
    long_label = models.CharField(max_length=100)
    scenario = models.ForeignKey(Scenario, on_delete=models.CASCADE, null=True, related_name="points")
    # Numerical values that must be provided for the point
    alpha = models.FloatField(
        verbose_name=const.ALPHA_NAME,
        validators=[
            validators.MinValueValidator(0)
        ]
    )
    beta_over_H = models.FloatField(
        verbose_name=const.BETA_OVER_H_NAME,
        validators=[
            validators.MinValueValidator(0)
        ]
    )
    # Optional numerical values that override the values from the model and scenario
    v_wall = models.FloatField(
        verbose_name=const.V_WALL_NAME,
        validators=[
            validators.MinValueValidator(0),
            validators.MaxValueValidator(1)
        ],
        null=True
    )
    T_star = models.FloatField(
        verbose_name=const.T_STAR_NAME,
        validators=[validators.MinValueValidator(0)],
        null=True
    )
    g_star = models.FloatField(
        verbose_name=const.G_STAR_NAME,
        validators=[validators.MinValueValidator(0)],
        null=True
    )

    # -----
    # Overridden methods
    # -----

    def __str__(self) -> str:
        return self.long_label

    def clean(self):
        super().clean()
        errors = {}
        if self.scenario is not None and self.scenario.model != self.model:
            errors["scenario"] = ValidationError("The scenario must be for the same model as the parameter choice.")
        if errors:
            raise ValidationError(errors)

    def get_absolute_url(self) -> str:
        return reverse("model_point_plot", kwargs={"model_id": self.model.id, "point_id": self.number})

    # -----
    # Properties
    # -----

    @property
    def g_star_value(self) -> float:
        return self.model.g_star if self.g_star is None else self.g_star

    @property
    def v_wall_value(self) -> float:
        return self.model.v_wall if self.v_wall is None else self.v_wall

    @property
    def T_star_value(self) -> float:
        return self.T_star \
            if self.T_star is not None \
            else self.scenario.T_star_value if self.scenario is not None \
            else self.model.T_star

    # -----
    # Methods
    # -----

    def csv(self, mission_profile: MissionProfile | None = None, engine: Engine = Engine.DEFAULT) -> str:
        if mission_profile is None:
            mission_profile = self.model.mission_profile
        return power_spectrum(
            T_star=self.T_star_value,
            g_star=self.g_star_value,
            v_wall=self.v_wall_value,
            alpha=self.alpha,
            beta_over_H=self.beta_over_H,
            engine=engine
        ).csv(mission_profile=mission_profile)

    def power_spectrum_figure(
            self,
            mission_profile: MissionProfile | None = None,
            engine: Engine = Engine.DEFAULT) -> Figure:
        spectrum = power_spectrum(
            T_star=self.T_star_value,
            g_star=self.g_star_value,
            v_wall=self.v_wall_value,
            alpha=self.alpha,
            beta_over_H=self.beta_over_H,
            engine=engine
        )
        return power_spectrum_figure(
            spectrum=spectrum,
            mission_profile=mission_profile
        )

    # def snr(
    #         self,
    #         adiabatic_ratio: float = const.DEFAULT_ADIABATIC_RATIO,
    #         f_min: float = const.DEFAULT_SNR_F_MIN,
    #         f_max: float = const.DEFAULT_SNR_F_MAX,
    #         mission_profile: MissionProfile = DEFAULT_MISSION_PROFILE,
    #         engine: Engine = Engine.DEFAULT) -> tuple[float, float]:
    #     snr, shock_time = snr_point(
    #         x=self.alpha, y=self.beta_over_H,
    #         T_star=self.T_star_value, g_star=self.g_star_value, v_wall=self.v_wall_value,
    #         adiabatic_ratio=adiabatic_ratio, f_min=f_min, f_max=f_max,
    #         mission_profile=mission_profile, engine=engine
    #     )
    #     return snr, shock_time

    def snr_comparison(
            self,
            engine1: Engine,
            engine2: Engine,
            mission_profile: MissionProfile | None = None) -> Figure:
        if mission_profile is None:
            mission_profile = self.model.mission_profile
        return snr_comparison(
            engine1=engine1,
            engine2=engine2,
            v_wall_snr=self.v_wall_value,
            T_star_snr=self.T_star_value,
            g_star_snr=self.g_star_value,
            alphas=self.alpha,
            beta_over_Hs=self.beta_over_H,
            labels=self.short_label,
            mission_profile=mission_profile
        )

    def snr_figure_alpha_beta(
            self,
            mission_profile: MissionProfile | None = None,
            engine: Engine = Engine.DEFAULT,
            filled: bool = False) -> Figure:
        if mission_profile is None:
            mission_profile = self.model.mission_profile
        return snr_figure_alpha_beta(
            v_wall_snr=self.v_wall_value,
            T_star_snr=self.T_star_value,
            g_star_snr=self.g_star_value,
            alphas=self.alpha,
            beta_over_Hs=self.beta_over_H,
            labels=self.short_label,
            mission_profile=mission_profile,
            huge_alpha=self.model.huge_alpha,
            engine=engine,

        )

    def snr_figure_ubarf_rstar(
            self,
            mission_profile: MissionProfile | None = None,
            engine: Engine = Engine.DEFAULT,
            filled: bool = False) -> Figure:
        if mission_profile is None:
            mission_profile = self.model.mission_profile
        return snr_figure_ubarf_rstar(
            v_wall_snr=self.v_wall_value,
            T_star_snr=self.T_star_value,
            g_star_snr=self.g_star_value,
            alphas=self.alpha,
            beta_over_Hs=self.beta_over_H,
            v_walls=self.v_wall_value,
            labels=self.short_label,
            mission_profile=mission_profile,
            huge_alpha=self.model.huge_alpha,
            engine=engine,
            filled=filled
        )

    class Meta:
        indexes = [models.Index(fields=["model", "number"])]
        ordering = ["model", "number"]
        unique_together = ["model", "number"]
