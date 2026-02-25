"""Particle physics models"""

import typing as tp

from django.core import validators
from django.db import models
from django.urls import reverse
from pandas import DataFrame

from ptplot.methods.models import point_data
from ptplot.models.const import NAME_MAX_LENGTH
from ptplot.science import const
from ptplot.science.mission_profile import MISSION_PROFILE_CHOICES, MissionProfile
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
        return MissionProfile.from_ind(self.mission_profile_ind)

    def point_data(self) -> DataFrame:
        return point_data(self.points.all())

    def point_data_by_scenario(self) -> "dict[Scenario, DataFrame]":
        return {scenario: scenario.point_data() for scenario in self.scenarios.prefetch_related("points").all()}

    def point_data_by_field(self):
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

    class Meta:
        indexes = [models.Index(fields=["name"])]
        ordering = ["name"]
