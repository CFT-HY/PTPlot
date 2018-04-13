from django import forms

class PTPlotForm(forms.Form):
    vw = forms.FloatField(label=r'Wall velocity $v_\mathrm{w}$',
                          min_value=0.0, max_value=1.0)
#    tstar = forms.FloatField(label=r'Phase transition temperature $T_*$',
#                             min_value=0.0)    
    alpha = forms.FloatField(label=r'Phase transition strength $\alpha$',
                             min_value=0.0)
    HoverBeta = forms.FloatField(label=r'Phase transition duration $H/\beta$',
                             min_value=0.0)
    
#    usetex = forms.BooleanField(label='Use TeX for labels (slow)?',
#                                initial=False,
#                                required=False)
