from django.core import validators
from django.db import models

from ptplot.models.const import NAME_MAX_LENGTH
from ptplot.science import const
from ptplot.science.mission_profile import MISSION_PROFILE_CHOICES, MissionProfile


class Model(models.Model):
    name = models.CharField(max_length=NAME_MAX_LENGTH, unique=True)
    description = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    vw = models.FloatField(
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
            mission_profile: int | MissionProfile = None,
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

    def __str__(self):
        return self.name

    @property
    def mission_profile(self) -> MissionProfile:
        return MissionProfile.from_ind(self.mission_profile_ind)

    class Meta:
        indexes = [models.Index(fields=["name"])]
        ordering = ["name"]
