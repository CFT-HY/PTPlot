from django import forms

class PTPlotForm(forms.Form):
    vw = forms.FloatField(label='Wall velocity $v_\mathrm{w}$',
                          min_value=0.0, max_value=1.0)
    tstar = forms.FloatField(label='Phase transition temperature $T_*$',
                             min_value=0.0)    
#    usetex = forms.BooleanField(label='Use TeX for labels (slow)?',
#                                initial=False,
#                                required=False)
