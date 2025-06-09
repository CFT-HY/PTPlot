from django.core import validators
from django.db import models

NAME_MAX_LENGTH: int = 200


class Model(models.Model):
    model_name = models.CharField(max_length=NAME_MAX_LENGTH, unique=True)
    model_description = models.TextField(blank=True)
    model_notes = models.TextField(blank=True)
    model_vw = models.FloatField(
        verbose_name="wall velocity",
        validators=[
            validators.MinValueValidator(0),
            validators.MaxValueValidator(1)
        ],
    )
    model_Tstar = models.FloatField(
        validators=[validators.MinValueValidator(0)]
    )
    model_gstar = models.FloatField(
        validators=[validators.MinValueValidator(0)]
    )
    model_MissionProfile = models.IntegerField(default=0)
    model_hugeAlpha = models.BooleanField(default=False)
    model_hasScenarios = models.BooleanField()

    def __str__(self):
        return self.model_name

    class Meta:
        indexes = [models.Index(fields=["model_name"])]
        ordering = ["model_name"]


class Scenario(models.Model):
    scenario_model = models.ForeignKey(Model, on_delete=models.CASCADE)
    scenario_number = models.IntegerField()
    scenario_name = models.CharField(max_length=NAME_MAX_LENGTH)
    scenario_Tstar = models.FloatField(
        validators=[validators.MinValueValidator(0)],
        null=True
    )
    scenario_description = models.TextField(blank=True)

    def __str__(self):
        return self.scenario_name

    class Meta:
        indexes = [models.Index(fields=["scenario_name"])]
        ordering = ["scenario_model", "scenario_number"]
        unique_together = ["scenario_model", "scenario_number"]


class ParameterChoice(models.Model):
    model = models.ForeignKey(Model, on_delete=models.CASCADE)
    number = models.IntegerField()
    point_shortlabel = models.CharField(max_length=2)
    point_longlabel = models.CharField(max_length=100)
    vw = models.FloatField(
        verbose_name="wall velocity",
        validators=[
            validators.MinValueValidator(0),
            validators.MaxValueValidator(1)
        ],
        null=True
    )
    alpha = models.FloatField(
        validators=[
            validators.MinValueValidator(0)
        ]
    )
    BetaoverH = models.FloatField(
        validators=[
            validators.MinValueValidator(0)
        ]
    )
    Tstar = models.FloatField(
        validators=[validators.MinValueValidator(0)],
        null=True
    )
    gstar = models.FloatField(
        validators=[validators.MinValueValidator(0)],
        null=True
    )
    scenario = models.ForeignKey(Scenario, on_delete=models.CASCADE, null=True)

    def __str__(self):
        return self.point_longlabel

    class Meta:
        indexes = [models.Index(fields=["model", "number"])]
        ordering = ["model", "number"]
        unique_together = ["model", "number"]
