from django.db import models

from .science.precomputed import precomputed_gstar, precomputed_Tn

# Create your models here.

class Theory(models.Model):
    theory_name = models.CharField(max_length=200)
    theory_description = models.TextField(null=True)
    
class ParameterChoice(models.Model):
    theory = models.ForeignKey(Theory, on_delete=models.CASCADE)
    point_shortlabel = models.CharField(max_length=2)
    vw = models.FloatField()
    alpha = models.FloatField()
    HoverBeta = models.FloatField()
    SNRcurve = models.IntegerField(default=0)


    def update_snrchoice(self):
        self.gstar = precomputed_gstar[self.SNRcurve]
        self.Tn = precomputed_Tn[self.SNRcurve]
