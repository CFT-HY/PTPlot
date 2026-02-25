"""Scenarios for particle physics models"""

from django.core import validators
from django.db import models
from django.urls import reverse
from pandas import DataFrame

from ptplot.methods.models import point_data
from ptplot.models.const import NAME_MAX_LENGTH
from ptplot.models.model import Model
from ptplot.science import const


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

    def __str__(self) -> str:
        return self.name

    def get_absolute_url(self) -> str:
        return reverse("model_scenario_plot", kwargs={"model_id": self.model.id, "scenario_id": self.number})

    def point_data(self) -> DataFrame:
        return point_data(self.points.all())

    @property
    def T_star_value(self) -> float:
        return self.model.T_star if self.T_star is None else self.T_star

    class Meta:
        indexes = [models.Index(fields=["name"])]
        ordering = ["model", "number"]
        unique_together = ["model", "number"]
