
from django.db import models

from .science.precomputed import precomputed_gstar, precomputed_Tn

# Create your models here.

class Theory(models.Model):
    theory_name = models.CharField(max_length=200)
    theory_description = models.TextField(null=True)
    theory_notes = models.TextField(null=True)
    theory_vw = models.FloatField()
    theory_Tstar = models.FloatField()
    theory_gstar = models.FloatField()
    theory_Senscurve = models.IntegerField(default=0)
    theory_hasScenarios = models.BooleanField()

class Scenario(models.Model):
    scenario_theory = models.ForeignKey(Theory, on_delete=models.CASCADE)
    scenario_number = models.IntegerField()
    scenario_name = models.CharField(max_length=200)
    scenario_description = models.TextField(null=True)
    
class ParameterChoice(models.Model):
    theory = models.ForeignKey(Theory, on_delete=models.CASCADE)
    number = models.IntegerField()
    point_shortlabel = models.CharField(max_length=2)
    point_longlabel = models.CharField(max_length=100)
    vw = models.FloatField(null=True)
    alpha = models.FloatField()
    BetaoverH = models.FloatField()
    Tstar = models.FloatField(null=True)
    gstar = models.FloatField(null=True)
    scenario = models.ForeignKey(Scenario, on_delete=models.CASCADE, null=True)
