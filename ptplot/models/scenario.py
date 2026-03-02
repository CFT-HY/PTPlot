"""Scenarios for particle physics models"""

from django.core import validators
from django.db import models
from django.urls import reverse
from matplotlib.figure import Figure
from pandas import DataFrame

from ptplot.methods.models import point_data
from ptplot.models.const import NAME_MAX_LENGTH
from ptplot.models.model import Model
from ptplot.science import const
from ptplot.science.mission_profile import MissionProfile
from ptplot.science.plot.snr_alpha_beta import snr_figure_alpha_beta
from ptplot.science.plot.snr_comparison import snr_comparison
from ptplot.science.plot.snr_histogram import snr_histogram
from ptplot.science.plot.snr_ubarf_rstar import snr_figure_ubarf_rstar
from ptplot.science.spectrum import Engine


class Scenario(models.Model):
    """A scenario with a particular $T_*$ for a particle physics model"""
    model = models.ForeignKey(Model, on_delete=models.CASCADE, related_name="scenarios")
    number = models.IntegerField()
    name = models.CharField(max_length=NAME_MAX_LENGTH)
    T_star = models.FloatField(
        verbose_name=const.T_STAR_NAME,
        validators=[validators.MinValueValidator(0)],
        null=True
    )
    description = models.TextField(blank=True)

    # -----
    # Overridden methods
    # -----

    def __str__(self) -> str:
        return self.name

    def get_absolute_url(self) -> str:
        return reverse("model_scenario_plot", kwargs={"model_id": self.model.id, "scenario_id": self.number})

    # -----
    # Properties
    # -----

    @property
    def T_star_value(self) -> float:
        return self.model.T_star if self.T_star is None else self.T_star

    # -----
    # Methods
    # -----

    def point_data(self) -> DataFrame:
        return point_data(self.points.all())

    def snr_comparison(
            self,
            engine1: Engine,
            engine2: Engine,
            mission_profile: MissionProfile | None = None) -> Figure:
        if mission_profile is None:
            mission_profile = self.model.mission_profile
        data = self.point_data()
        return snr_comparison(
            engine1=engine1,
            engine2=engine2,
            v_wall_snr=self.model.v_wall,
            T_star_snr=self.T_star_value,
            g_star_snr=self.model.g_star,
            alphas=data["alpha_n"].values,
            beta_over_Hs=data["beta_over_H"].values,
            labels=data["label"].to_list(),
            titles=self.name,
            mission_profile=mission_profile
        )

    def snr_figure_alpha_beta(
            self,
            mission_profile: MissionProfile | None = None,
            engine: Engine = Engine.DEFAULT) -> Figure:
        if mission_profile is None:
            mission_profile = self.model.mission_profile
        data = self.point_data()
        return snr_figure_alpha_beta(
            v_wall_snr=self.model.v_wall,
            T_star_snr=self.T_star_value,
            g_star_snr=self.model.g_star,
            alphas=data["alpha_n"].values,
            beta_over_Hs=data["beta_over_H"].values,
            labels=data["label"].to_list(),
            titles=self.name,
            mission_profile=mission_profile,
            huge_alpha=self.model.huge_alpha,
            engine=engine
        )

    def snr_figure_ubarf_rstar(
            self,
            mission_profile: MissionProfile | None = None,
            engine: Engine = Engine.DEFAULT) -> Figure:
        if mission_profile is None:
            mission_profile = self.model.mission_profile
        data = self.point_data()
        return snr_figure_ubarf_rstar(
            v_wall_snr=self.model.v_wall,
            T_star_snr=self.T_star_value,
            g_star_snr=self.model.g_star,
            v_walls=data["v_wall"].values,
            alphas=data["alpha_n"].values,
            beta_over_Hs=data["beta_over_H"].values,
            labels=data["label"].to_list(),
            titles=self.name,
            mission_profile=mission_profile,
            huge_alpha=self.model.huge_alpha,
            engine=engine
        )

    def snr_histogram(self, mission_profile: MissionProfile | None = None) -> Figure:
        if mission_profile is None:
            mission_profile = self.model.mission_profile
        data = self.point_data()
        return snr_histogram(
            v_wall=data["v_wall"].values,
            alpha_n=data["alpha_n"].values,
            beta_over_H=data["beta_over_H"].values,
            T_star=data["T_star"].values,
            g_star=data["g_star"].values,
            labels=data["label"].to_list(),
            titles=self.name,
            mission_profile=mission_profile,
            # engines=[form.cleaned_data["engine"]]
        )

    class Meta:
        indexes = [models.Index(fields=["name"])]
        ordering = ["model", "number"]
        unique_together = ["model", "number"]
