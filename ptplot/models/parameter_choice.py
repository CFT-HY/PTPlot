"""Parameter choices for particle physics models"""

from django.core import validators
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse

from ptplot.models.model import Model
from ptplot.models.scenario import Scenario
from ptplot.science import const


class ParameterChoice(models.Model):
    """A parameter choice, aka. a point, for a particle physics model"""
    model = models.ForeignKey(Model, on_delete=models.CASCADE, related_name="points")
    number = models.IntegerField()
    short_label = models.CharField(max_length=2)
    long_label = models.CharField(max_length=100)
    v_wall = models.FloatField(
        verbose_name=const.V_WALL_NAME,
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

    def clean(self):
        super().clean()
        errors = {}
        if self.scenario is not None and self.scenario.model != self.model:
            errors["scenario"] = ValidationError("The scenario must be for the same model as the parameter choice.")
        if errors:
            raise ValidationError(errors)

    def get_absolute_url(self) -> str:
        return reverse("model_point_plot", kwargs={"model_id": self.model.id, "point_id": self.number})

    @property
    def v_wall_value(self) -> float:
        return self.model.v_wall if self.v_wall is None else self.v_wall

    @property
    def T_star_value(self) -> float:
        return self.T_star \
            if self.T_star is not None \
            else self.scenario.T_star if (self.scenario is not None and self.scenario.T_star is not None) \
            else self.model.T_star

    @property
    def g_star_value(self) -> float:
        return self.model.g_star if self.g_star is None else self.g_star

    class Meta:
        indexes = [models.Index(fields=["model", "number"])]
        ordering = ["model", "number"]
        unique_together = ["model", "number"]
