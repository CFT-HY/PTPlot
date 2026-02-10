"""Scenarios for particle physics models"""

from django.core import validators
from django.db import models

from ptplot.models.const import NAME_MAX_LENGTH
from ptplot.models.model import Model
from ptplot.science import const


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
