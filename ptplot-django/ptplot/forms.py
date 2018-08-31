from django import forms

from .models import *

from .science.precomputed import precomputed_gstar, precomputed_Tn, precomputed_filenames, precomputed_labels, available_sensitivitycurves, available_labels

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
    precomputed_choices = [(i, r'%s with $g_\star = %g$, $T_n = %g\, \mathrm{GeV}$' % (label,gstar,Tn)) for i, (label, gstar, Tn) in enumerate(zip(precomputed_labels, precomputed_gstar, precomputed_Tn))]

    available_senscurves = [(i, label) for i, label in enumerate(available_labels)]

    
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
    PSONLY, PSANDSNR = 'psonly', 'psandsnr'
    PS_CHOICES = (
        (PSONLY, 'Plot the power spectrum only'),
        (PSANDSNR, 'Plot the power spectrum and SNR curves'),
    )
    pschoices = forms.ChoiceField(choices=PS_CHOICES, widget=forms.RadioSelect)
    
    SNRcurve = forms.ChoiceField(label=r'SNR curve',
                                 choices=precomputed_choices,
                                 required=False)

    Senscurve = forms.ChoiceField(label=r'Sensitivity curve',
                                  choices=available_senscurves,
                                  required=False)
    Tstar = forms.FloatField(label=r'Transition temperature $T_\star$',
                             min_value=0.0,
                             localize=False,
                             required=False)
    Gstar = forms.FloatField(label=r'Degrees of freedom $g_\star$',
                             min_value=0.0,
                             localize=False,
                             required=False)

    
#    usetex = forms.BooleanField(label='Use TeX for labels (slow)?',
#                                initial=False,
#                                required=False)


    def __init__(self, data=None, *args, **kwargs):
        super(PTPlotForm, self).__init__(data, *args, **kwargs)

        # If 'later' is chosen, set send_date as required
        if data and data.get('pschoices', None) == self.PSONLY:
            self.fields['Tstar'].required = True
            self.fields['Gstar'].required = True
            self.fields['Senscurve'].required = True

        if data and data.get('pschoices', None) == self.PSANDSNR:
            self.fields['SNRcurve'].required = True

            

class MultipleForm(forms.Form):
    precomputed_choices = [(i, r'$g_\star = %g$, $T_n = %g\, \mathrm{GeV}$' % (gstar,Tn)) for i, (gstar, Tn) in enumerate(zip(precomputed_gstar, precomputed_Tn))]
   
    vw = forms.FloatField(label=r'Wall velocity $v_\mathrm{w}$',
                          min_value=0.0, max_value=1.0,
                          validators=[validate_velocity],
                          localize=False)
    SNRcurve = forms.ChoiceField(label=r'SNR curve',
                                 choices=precomputed_choices)
    table = forms.CharField(label=r'Input table', widget=forms.Textarea,
                            initial="alpha,Hoverbeta,label")

class ParameterChoiceForm(forms.Form):

    theories = []
    
    try:
        theories = Theory.objects.all()
    except:
        pass
        
    for theory in theories:
        sys.stderr.write(theory.theory_name + '\n')

    underlying_theory = forms.ChoiceField(label=r'Theory',
                                          choices=[(theory.id,theory.theory_name) for theory in theories])

    precomputed_choices = [(i, r'$g_\star = %g$, $T_n = %g\, \mathrm{GeV}$' % (gstar,Tn)) for i, (gstar, Tn) in enumerate(zip(precomputed_gstar, precomputed_Tn))]
   
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
