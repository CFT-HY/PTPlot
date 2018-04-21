from django import forms

from .models import *

from .science.precomputed import precomputed_hstar, precomputed_Tn, precomputed_filenames

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

import sys

def validate_velocity(value):
    if not ((value > 0.0) and (value <= 1.0)):
        raise ValidationError(
            _('%(value)s must be greater than zero and less than or equal to 1'),
            params={'value': value},
            )

class PTPlotForm(forms.Form):
    precomputed_choices = [(i, r'$h_\star = %g$, $T_n = %g\, \mathrm{GeV}$' % (hstar,Tn)) for i, (hstar, Tn) in enumerate(zip(precomputed_hstar, precomputed_Tn))]
   
    vw = forms.FloatField(label=r'Wall velocity $v_\mathrm{w}$',
                          min_value=0.0, max_value=1.0,
                          validators=[validate_velocity],
                          localize=False)
#    tstar = forms.FloatField(label=r'Phase transition temperature $T_*$',
#                             min_value=0.0)    
    alpha = forms.FloatField(label=r'Phase transition strength $\alpha$',
                             min_value=0.0,
                             localize=False)
    HoverBeta = forms.FloatField(label=r'Phase transition duration $H/\beta$',
                                 min_value=0.0,
                                 localize=False)
    SNRcurve = forms.ChoiceField(label=r'SNR curve',
                                 choices=precomputed_choices)
    
#    usetex = forms.BooleanField(label='Use TeX for labels (slow)?',
#                                initial=False,
#                                required=False)


class ParameterChoiceForm(forms.Form):
    theories = Theory.objects.all()

    for theory in theories:
        sys.stderr.write(theory.theory_name + '\n')

    underlying_theory = forms.ChoiceField(label=r'Theory',
                                          choices=[(theory.id,theory.theory_name) for theory in theories])

    precomputed_choices = [(i, r'$h_\star = %g$, $T_n = %g\, \mathrm{GeV}$' % (hstar,Tn)) for i, (hstar, Tn) in enumerate(zip(precomputed_hstar, precomputed_Tn))]
   
    vw = forms.FloatField(label=r'Wall velocity $v_\mathrm{w}$',
                          min_value=0.0, max_value=1.0,
                          validators=[validate_velocity],
                          localize=False)
#    tstar = forms.FloatField(label=r'Phase transition temperature $T_*$',
#                             min_value=0.0)    
    alpha = forms.FloatField(label=r'Phase transition strength $\alpha$',
                             min_value=0.0,
                             localize=False)
    HoverBeta = forms.FloatField(label=r'Phase transition duration $H/\beta$',
                                 min_value=0.0,
                                 localize=False)
    SNRcurve = forms.ChoiceField(label=r'SNR curve',
                                 choices=precomputed_choices)
