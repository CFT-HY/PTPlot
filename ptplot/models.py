from django.core import validators
from django.db import models

from ptplot.science import const
from ptplot.science.precomputed import AVAILABLE_LABELS

NAME_MAX_LENGTH: int = 200


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
    mission_profile = models.IntegerField(default=0)
    huge_alpha = models.BooleanField(default=False)
    has_scenarios = models.BooleanField()

    def __str__(self):
        return self.name

    def mission_profile_label(self) -> str:
        return AVAILABLE_LABELS[self.mission_profile]

    class Meta:
        indexes = [models.Index(fields=["name"])]
        ordering = ["name"]


class Scenario(models.Model):
    model = models.ForeignKey(Model, on_delete=models.CASCADE, related_name="scenarios")
    number = models.IntegerField()
    name = models.CharField(max_length=NAME_MAX_LENGTH)
    T_star = models.FloatField(
        verbose_name=const.T_STAR_NAME,
        validators=[validators.MinValueValidator(0)],
        null=True
    )
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

    @property
    def T_star_value(self) -> float:
        return self.model.T_star if self.T_star is None else self.T_star

    class Meta:
        indexes = [models.Index(fields=["name"])]
        ordering = ["model", "number"]
        unique_together = ["model", "number"]


class ParameterChoice(models.Model):
    model = models.ForeignKey(Model, on_delete=models.CASCADE, related_name="points")
    number = models.IntegerField()
    short_label = models.CharField(max_length=2)
    long_label = models.CharField(max_length=100)
    vw = models.FloatField(
        verbose_name=const.VW_NAME,
        validators=[
            validators.MinValueValidator(0),
            validators.MaxValueValidator(1)
        ],
        null=True
    )
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
    scenario = models.ForeignKey(Scenario, on_delete=models.CASCADE, null=True, related_name="points")

    def __str__(self):
        return self.long_label

    @property
    def vw_value(self) -> float:
        return self.model.vw if self.vw is None else self.vw

    @property
    def T_star_value(self) -> float:
        return self.model.T_star if self.T_star is None else self.T_star

    @property
    def g_star_value(self) -> float:
        return self.model.g_star if self.g_star is None else self.g_star

    class Meta:
        indexes = [models.Index(fields=["model", "number"])]
        ordering = ["model", "number"]
        unique_together = ["model", "number"]
