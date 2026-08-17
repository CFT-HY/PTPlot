"""Particle physics models"""

import typing as tp

from django.core import validators
from django.db import models
from django.urls import reverse
from matplotlib.figure import Figure
from pandas import DataFrame
from pttools.speedup import MAX_WORKERS_DEFAULT

from ptplot.methods.models import point_data
from ptplot.models.const import NAME_MAX_LENGTH
from ptplot.science import const
from ptplot.science.mission_profile import MISSION_PROFILE_CHOICES, MissionProfile
from ptplot.science.plot.snr_alpha_beta import snr_figure_alpha_beta
from ptplot.science.plot.snr_comparison import snr_comparison
from ptplot.science.plot.snr_histogram import snr_histogram
from ptplot.science.plot.snr_ubarf_rstar import snr_figure_ubarf_rstar
from ptplot.science.spectrum import Engine
import ptplot.science.type_hints as th

if tp.TYPE_CHECKING:
    from ptplot.models.scenario import Scenario


class Model(models.Model):
    """A particle physics model"""
    name = models.CharField(max_length=NAME_MAX_LENGTH, unique=True)
    slug = models.SlugField(max_length=NAME_MAX_LENGTH, unique=True)
    description = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    v_wall = models.FloatField(
        verbose_name="wall velocity",
        validators=[
            validators.MinValueValidator(0),
            validators.MaxValueValidator(1)
        ],
    )
    T_star = models.FloatField(
        verbose_name=const.T_STAR_NAME,
        validators=[validators.MinValueValidator(0)]
    )
    g_star = models.FloatField(
        verbose_name=const.G_STAR_NAME,
        validators=[validators.MinValueValidator(0)]
    )
    mission_profile_ind = models.IntegerField(default=0, choices=MISSION_PROFILE_CHOICES)
    huge_alpha = models.BooleanField(
        verbose_name=const.HUGE_ALPHA_NAME,
        default=False
    )
    has_scenarios = models.BooleanField()

    def __init__(
            self,
            *args,
            mission_profile: int | MissionProfile | None = None,
            **kwargs):
        if mission_profile is not None:
            if "mission_profile_ind" in kwargs:
                raise ValueError("Cannot set both mission_profile and mission_profile_ind.")
            if isinstance(mission_profile, MissionProfile):
                kwargs["mission_profile_ind"] = mission_profile.ind
            elif isinstance(mission_profile, int):
                kwargs["mission_profile_ind"] = mission_profile
            else:
                raise ValueError("mission_profile must be MissionProfile or int.")
        super().__init__(*args, **kwargs)

    def __str__(self) -> str:
        return self.name

    def get_absolute_url(self) -> str:
        return reverse("model_detail", kwargs={"model_id": self.id})

    @property
    def mission_profile(self) -> MissionProfile:
        """Get the mission profile object"""
        return MissionProfile.from_ind(self.mission_profile_ind)

    def point_data(self) -> DataFrame:
        """Get the data of the points of this model as a DataFrame"""
        return point_data(self.points.all())

    def point_data_by_scenario(self) -> "dict[Scenario, DataFrame]":
        """Get the data of the points of this model by scenario"""
        return {scenario: scenario.point_data() for scenario in self.scenarios.prefetch_related("points").all()}

    def point_data_by_field(self) \
            -> tuple[th.FloatArr1D, th.FloatArr1D, th.FloatArr1D, th.FloatArr1D, th.FloatArr1D, list[str], str]:
        """Get the data of the points of this model as arrays of each field"""
        data = self.point_data()
        v_wall = data["v_wall"].values
        alpha = data["alpha_n"].values
        beta_over_H = data["beta_over_H"].values
        T_star = data["T_star"].values
        g_star = data["g_star"].values
        labels = data["label"].to_list()
        titles = self.name

        return v_wall, alpha, beta_over_H, T_star, g_star, labels, titles

    def point_data_by_field_and_scenario(self) -> tuple[
                th.FloatArr1DOrListOfArr1D,
                th.FloatArr1DOrListOfArr1D,
                th.FloatArr1DOrListOfArr1D,
                th.FloatArr1DOrListOfArr1D,
                th.FloatArr1DOrListOfArr1D,
                list[list[str]] | list[str],
                list[str] | str]:
        """Get the data of the points of this model as arrays of each field, in lists by scenario"""
        if not self.has_scenarios:
            return self.point_data_by_field()
        scenarios = self.scenarios.prefetch_related("points").all()
        v_wall = []
        alpha = []
        beta_over_H = []
        T_star = []
        g_star = []
        labels = []
        titles = []

        for scenario in scenarios:
            data = scenario.point_data()
            v_wall.append(data["v_wall"].values)
            alpha.append(data["alpha_n"].values)
            beta_over_H.append(data["beta_over_H"].values)
            T_star.append(data["T_star"].values)
            g_star.append(data["g_star"].values)
            labels.append(data["label"].to_list())
            titles.append(scenario.name)

        return v_wall, alpha, beta_over_H, T_star, g_star, labels, titles

    def snr_comparison(
            self,
            engine1: Engine,
            engine2: Engine,
            mission_profile: MissionProfile | None = None,
            max_workers: int = MAX_WORKERS_DEFAULT) -> Figure:
        if mission_profile is None:
            mission_profile = self.mission_profile
        v_wall, alpha, beta_over_H, T_star, g_star, labels, titles = self.point_data_by_field_and_scenario()
        return snr_comparison(
            engine1=engine1,
            engine2=engine2,
            v_wall_snr=self.v_wall,
            T_star_snr=self.T_star,
            g_star_snr=self.g_star,
            alphas=alpha,
            beta_over_Hs=beta_over_H,
            labels=labels,
            titles=titles,
            mission_profile=mission_profile,
            max_workers=max_workers
        )

    def snr_figure_alpha_beta(
            self,
            mission_profile: MissionProfile | None = None,
            engine: Engine = Engine.DEFAULT,
            filled: bool = False,
            max_workers: int = MAX_WORKERS_DEFAULT) -> Figure:
        if mission_profile is None:
            mission_profile = self.mission_profile
        v_wall, alpha, beta_over_H, T_star, g_star, labels, titles = self.point_data_by_field_and_scenario()
        return snr_figure_alpha_beta(
            v_wall_snr=self.v_wall,
            T_star_snr=self.T_star,
            g_star_snr=self.g_star,
            alphas=alpha,
            beta_over_Hs=beta_over_H,
            labels=labels,
            titles=titles,
            mission_profile=mission_profile,
            huge_alpha=self.huge_alpha,
            engine=engine,
            filled=filled,
            max_workers=max_workers
        )

    def snr_figure_ubarf_rstar(
            self,
            mission_profile: MissionProfile | None = None,
            engine: Engine = Engine.DEFAULT,
            filled: bool = False,
            max_workers: int = MAX_WORKERS_DEFAULT) -> Figure:
        if mission_profile is None:
            mission_profile = self.mission_profile
        v_walls, alphas, beta_over_H, T_star, g_star, labels, titles = self.point_data_by_field_and_scenario()
        return snr_figure_ubarf_rstar(
            v_wall_snr=self.v_wall,
            T_star_snr=self.T_star,
            g_star_snr=self.g_star,
            v_walls=v_walls,
            alphas=alphas,
            beta_over_Hs=beta_over_H,
            labels=labels,
            titles=titles,
            mission_profile=mission_profile,
            huge_alpha=self.huge_alpha,
            engine=engine,
            filled=filled,
            max_workers=max_workers
        )

    def snr_histogram(self, mission_profile: MissionProfile | None = None) -> Figure:
        if mission_profile is None:
            mission_profile = self.mission_profile
        v_wall, alpha, beta_over_H, T_star, g_star, labels, titles = self.point_data_by_field()
        return snr_histogram(
            v_wall=v_wall, alpha_n=alpha, beta_over_H=beta_over_H, T_star=T_star, g_star=g_star,
            labels=labels, titles=titles,
            mission_profile=mission_profile,
            # engines=[form.cleaned_data["engine"]]
        )

    class Meta:
        indexes = [models.Index(fields=["name"])]
        ordering = ["name"]
