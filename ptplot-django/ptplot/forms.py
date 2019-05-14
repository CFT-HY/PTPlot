from django import forms

from .models import *

from .science.precomputed import available_sensitivitycurves, available_labels

from django.core.exceptions import ValidationError
from django.db.utils import OperationalError
from django.utils.translation import gettext_lazy as _

import sys

def validate_velocity(value):
    if not ((value > 0.0) and (value <= 1.0)):
        raise ValidationError(
            _('%(value)s must be greater than zero and less than or equal to 1'),
            params={'value': value},
            )

class PTPlotForm(forms.Form):
    available_senscurves = [(i, label) for i, label in enumerate(available_labels)]

    
    vw = forms.FloatField(label=r'Wall velocity $v_\mathrm{w}$',
                          min_value=0.0, max_value=1.0,
                          validators=[validate_velocity],
                          localize=False)

    alpha = forms.FloatField(label=r'Phase transition strength $\alpha_\theta$',
                             min_value=0.0,
                             localize=False)
    BetaoverH = forms.FloatField(label=r'Inverse phase transition duration $\beta/H_*$',
                                 min_value=0.0,
                                 localize=False)

    Tstar = forms.FloatField(label=r'Transition temperature $T_\star$',
                             min_value=0.0,
                             localize=False)

    gstar = forms.FloatField(label=r'Degrees of freedom $g_\star$',
                             min_value=0.0,
                             localize=False)

    Senscurve = forms.ChoiceField(label=r'Sensitivity curve',
                                  choices=available_senscurves)

    
#    usetex = forms.BooleanField(label='Use TeX for labels (slow)?',
#                                initial=False,
#                                required=False)


    def __init__(self, data=None, *args, **kwargs):
        super(PTPlotForm, self).__init__(data, *args, **kwargs)


            

class MultipleForm(forms.Form):
    available_senscurves = [(i, label) for i, label in enumerate(available_labels)]
   
    vw = forms.FloatField(label=r'Wall velocity $v_\mathrm{w}$',
                          min_value=0.0, max_value=1.0,
                          validators=[validate_velocity],
                          localize=False)
    Tstar = forms.FloatField(label=r'Transition temperature $T_\star$',
                             min_value=0.0,
                             localize=False)

    gstar = forms.FloatField(label=r'Degrees of freedom $g_\star$',
                             min_value=0.0,
                             localize=False)

    Senscurve = forms.ChoiceField(label=r'Sensitivity curve',
                                  choices=available_senscurves)

    table = forms.CharField(label=r'Input table', widget=forms.Textarea,
                            initial="#alpha_theta,BetaOverH,label")

class ParameterChoiceForm(forms.Form):

    def __init__(self):
    
        self.theories = []
    
        try:
            self.theories = Theory.objects.all()
        except:
            pass
        
        for theory in self.theories:
            sys.stderr.write(theory.theory_name + '\n')

            self.underlying_theory = forms.ChoiceField(label=r'Theory',
                                                       choices=[(theory.id,theory.theory_name) for theory in theories])
            
            self.precomputed_choices = [(i, r'$g_\star = %g$, $T_n = %g\, \mathrm{GeV}$' % (gstar,Tn)) for i, (gstar, Tn) in enumerate(zip(precomputed_gstar, precomputed_Tn))]
            
            self.vw = forms.FloatField(label=r'Wall velocity $v_\mathrm{w}$',
                                       min_value=0.0, max_value=1.0,
                                       validators=[validate_velocity],
                                       localize=False)
            #    tstar = forms.FloatField(label=r'Phase transition temperature $T_*$',
            #                             min_value=0.0)    
            self.alpha = forms.FloatField(label=r'Phase transition strength $\alpha_\theta$',
                                          min_value=0.0,
                                          localize=False)
            self.BetaoverH = forms.FloatField(label=r'Inverse phase transition duration $\beta/H_*$',
                                              min_value=0.0,
                                              localize=False)
            self.SNRcurve = forms.ChoiceField(label=r'Sensitivity curve',
                                              choices=available_labels)
            
