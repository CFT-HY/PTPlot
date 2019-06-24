
from django.db import models

# from .science.precomputed import precomputed_gstar, precomputed_Tn

# Create your models here.

class Model(models.Model):
    model_name = models.CharField(max_length=200)
    model_description = models.TextField(null=True)
    model_notes = models.TextField(null=True)
    model_vw = models.FloatField()
    model_Tstar = models.FloatField()
    model_gstar = models.FloatField()
    model_Senscurve = models.IntegerField(default=0)
    model_hasScenarios = models.BooleanField()

class Scenario(models.Model):
    scenario_model = models.ForeignKey(Model, on_delete=models.CASCADE)
    scenario_number = models.IntegerField()
    scenario_name = models.CharField(max_length=200)
    scenario_Tstar = models.FloatField(null=True)
    scenario_description = models.TextField(null=True)
    
class ParameterChoice(models.Model):
    model = models.ForeignKey(Model, on_delete=models.CASCADE)
    number = models.IntegerField()
    point_shortlabel = models.CharField(max_length=2)
    point_longlabel = models.CharField(max_length=100)
    vw = models.FloatField(null=True)
    alpha = models.FloatField()
    BetaoverH = models.FloatField()
    Tstar = models.FloatField(null=True)
    gstar = models.FloatField(null=True)
    scenario = models.ForeignKey(Scenario, on_delete=models.CASCADE, null=True)
