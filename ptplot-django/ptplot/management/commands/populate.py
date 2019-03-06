from django.core.management.base import BaseCommand
from ptplot.models import *

import numpy as np

class Command(BaseCommand):
    args = '<foo bar ...>'
    help = 'our help string comes here'

    def _populate_db(self):
        print('populating DB...')
        
        singlet_theory \
            = Theory(theory_name=r'Singlet (Higgs Portal) benchmark points',
                                  theory_description=r''' 
Real singlet extension of the Standard Model with $Z_2$
symmetry, with $m_S = 250\, \mathrm{GeV}$.''',
                    theory_notes=r'''Benchmark points from https://arxiv.org/abs/1512.06239. Data
from Table 3, see potential, Eq. (30), for details of potential
parameters $(a_2,b_4)$. $T_*$ is taken to be $50\, \mathrm{GeV}$ for the plot.
                                ''',
                     theory_Tstar=50,
                     theory_gstar=106.75,
                     theory_vw=0.95,
                     theory_Senscurve=0)
        singlet_theory.save()

        
        pA = ParameterChoice(theory=singlet_theory,
                             point_shortlabel=r'A',
                             point_longlabel=r'$(a_2,b_4) = (2.8,2.1)$',
                             Tstar=70.6,
                             alpha=0.09,
                             BetaoverH=47.35)

        pA.save()
        
        pB = ParameterChoice(theory=singlet_theory,
                             point_shortlabel=r'B',
                             point_longlabel=r'$(a_2,b_4) = (2.9,2.6)$',
                             Tstar=65.2,
                             alpha=0.12,
                             BetaoverH=29.96)

        pB.save()
        
        
        pC = ParameterChoice(theory=singlet_theory,
                             point_shortlabel=r'C',
                             point_longlabel=r'$(a_2,b_4) = (3.0,3.3)$',                             
                             Tstar=49.6,
                             alpha=0.17,
                             BetaoverH=12.54)

        pC.save()

        pD = ParameterChoice(theory=singlet_theory,
                             point_shortlabel=r'D',
                             point_longlabel=r'$(a_2,b_4) = (3.1,4.0)$',
                             Tstar=56.4,
                             alpha=0.20,
                             BetaoverH=6.42)

        pD.save()
       
        print('done populating.')
        print('NOTE: run python3 manage.py flush to clear tables')

    def handle(self, *args, **options):
        self._populate_db()
