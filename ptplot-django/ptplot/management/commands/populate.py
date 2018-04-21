from django.core.management.base import BaseCommand
from ptplot.models import Theory, ParameterChoice

class Command(BaseCommand):
    args = '<foo bar ...>'
    help = 'our help string comes here'

    def _populate_db(self):
        # note python3 manage.py flush to clear tables
        
        singlet_theory = Theory(theory_name='Singlet',
                                theory_description='Singlet extension of the Standard Model')
        singlet_theory.save()

        pA = ParameterChoice(theory=singlet_theory,
                             point_shortlabel='A',
                             vw=0.5,
                             alpha=0.037,
                             HoverBeta=0.0036,
                             SNRcurve=0)
        pA.save()
        
        pB = ParameterChoice(theory=singlet_theory,
                             point_shortlabel='B',
                             vw=0.5,
                             alpha=0.066,
                             HoverBeta=0.0094,
                             SNRcurve=0)
        pB.save()
        
        
        pC = ParameterChoice(theory=singlet_theory,
                             point_shortlabel='C',
                             vw=0.5,
                             alpha=0.105,
                             HoverBeta=0.0301,
                             SNRcurve=0)
        pC.save()

        pD = ParameterChoice(theory=singlet_theory,
                             point_shortlabel='D',
                             vw=0.5,
                             alpha=0.143,
                             HoverBeta=0.17,
                             SNRcurve=0)
        pD.save()
       
        

    def handle(self, *args, **options):
        self._populate_db()
