from django.core.management.base import BaseCommand
from ptplot.models import *

import numpy as np

import os, string

filedir = os.path.dirname(os.path.realpath(__file__))


class Command(BaseCommand):
    args = '<foo bar ...>'
    help = 'our help string comes here'

    def _populate_db(self):
        print('populating DB...')
        
#         singlet_theory \
#             = Theory(theory_name=r'Singlet (Higgs Portal) benchmark points',
#                                   theory_description=r''' 
# Real singlet extension of the Standard Model with $Z_2$
# symmetry, with $m_S = 250\, \mathrm{GeV}$.''',
#                     theory_notes=r'''Benchmark points from https://arxiv.org/abs/1512.06239. Data
# from Table 3, see potential, Eq. (30), for details of potential
# parameters $(a_2,b_4)$. $T_*$ is taken to be $50\, \mathrm{GeV}$ for the plot.
#                                 ''',
#                      theory_Tstar=50,
#                      theory_gstar=106.75,
#                      theory_vw=0.95,
#                      theory_Senscurve=0,
#                      theory_hasScenarios=False)
#         singlet_theory.save()

        
#         pA = ParameterChoice(theory=singlet_theory,
#                              number=1,
#                              point_shortlabel=r'A',
#                              point_longlabel=r'$(a_2,b_4) = (2.8,2.1)$',
#                              Tstar=70.6,
#                              alpha=0.09,
#                              BetaoverH=47.35)

#         pA.save()
        
#         pB = ParameterChoice(theory=singlet_theory,
#                              number=2,
#                              point_shortlabel=r'B',
#                              point_longlabel=r'$(a_2,b_4) = (2.9,2.6)$',
#                              Tstar=65.2,
#                              alpha=0.12,
#                              BetaoverH=29.96)

#         pB.save()
        
        
#         pC = ParameterChoice(theory=singlet_theory,
#                              number=3,
#                              point_shortlabel=r'C',
#                              point_longlabel=r'$(a_2,b_4) = (3.0,3.3)$',                          
#                              Tstar=49.6,
#                              alpha=0.17,
#                              BetaoverH=12.54)

#         pC.save()

#         pD = ParameterChoice(theory=singlet_theory,
#                              number=4,
#                              point_shortlabel=r'D',
#                              point_longlabel=r'$(a_2,b_4) = (3.1,4.0)$',
#                              Tstar=56.4,
#                              alpha=0.20,
#                              BetaoverH=6.42)

#         pD.save()





        twohdm_josemi_theory = \
            Theory(theory_name=r'2HDM benchmark points',
                                  theory_description='''
                                  Description goes here''',
                   theory_notes=r'''Notes go here: equation for the potential, parameters, etc.''',
                   theory_Tstar=50,
                   theory_gstar=106.75,
                   theory_vw=0.9,
                   theory_Senscurve=0,
                   theory_hasScenarios=True)
        twohdm_josemi_theory.save()

        josemi_set_1 = \
            Scenario(scenario_theory=twohdm_josemi_theory,
                     scenario_number=1,
                     scenario_name="Set 1",
                     scenario_description=r'2HDM points which are currently allowed both for Type I and Type II 2HDM. For Type II, these will be probed by the LHC in the future, while for Type I the LHC will not be able to exclude these benchmarks, depending on the value of $\tan\beta$ (which does influence the strength of the PT).')
        josemi_set_1.save()
        
        josemi_points = np.genfromtxt(os.path.join(filedir, 'josemi_2hdm.txt'), delimiter=',',names=True)
        Tn = josemi_points['Tn']
        alpha_n = josemi_points['alpha_n']
        beta_H_n = josemi_points['beta_H_n']
        tanb = josemi_points['tanb']
        mH = josemi_points['mH']
        mA = josemi_points['mA']
        
        for i, (this_mH, this_mA, this_Tn, this_alpha_n, this_beta_H_n, this_tanb) in \
            enumerate(zip(mH, mA, Tn, alpha_n, beta_H_n, tanb)):
            point = ParameterChoice(theory=twohdm_josemi_theory,
                                    number=(i+1),
                                    point_longlabel=r'$(m_H,m_A) = (%d,%d) \, \mathrm{GeV}$, $\tan \beta = %d$' % (this_mH, this_mA, this_tanb),
                                    Tstar=this_Tn,
                                    alpha=this_alpha_n,
                                    BetaoverH=this_beta_H_n,
                                    scenario=josemi_set_1)

            point.save()


        josemi_set_2 = \
            Scenario(scenario_theory=twohdm_josemi_theory,
                     scenario_number=2,
                     scenario_name="Set 2",
                     scenario_description=r'2HDM points which are currently allowed for Type I 2HDM, but excluded for Type II 2HDM, by LHC searches.')
        josemi_set_2.save()
        
        josemi_points = np.genfromtxt(os.path.join(filedir, 'josemi_2hdm_set2.txt'), delimiter=',',names=True)
        Tn = josemi_points['Tn']
        alpha_n = josemi_points['alpha_n']
        beta_H_n = josemi_points['beta_H_n']
        tanb = josemi_points['tanb']
        mH = josemi_points['mH']
        mA = josemi_points['mA']
        
        for i, (this_mH, this_mA, this_Tn, this_alpha_n, this_beta_H_n, this_tanb) in \
            enumerate(zip(mH, mA, Tn, alpha_n, beta_H_n, tanb)):
            point = ParameterChoice(theory=twohdm_josemi_theory,
                                    number=(i+1),
                                    point_longlabel=r'$(m_H,m_A) = (%d,%d) \, \mathrm{GeV}$, $\tan \beta = %d$' % (this_mH, this_mA, this_tanb),
                                    Tstar=this_Tn,
                                    alpha=this_alpha_n,
                                    BetaoverH=this_beta_H_n,
                                    scenario=josemi_set_2)

            point.save()

            

        singlet_miki_theory = \
            Theory(theory_name=r'Singlet portal benchmark points',
                                  theory_description=r'''Benchmark points for the SM extended with a scalar singlet with
$Z_2$ symmetry.''',
                    theory_notes=r'''The new physics potential reads

$$\Delta V = \frac{1}{2}a_2 |H|^2 S^2 + \frac{1}{2} b_2 S^2 + \frac{1}{4} 
b_4 S^4.$$

The parameter $m$ below stands for the physical mass of the singlet.
For each pair $(m, a_2)$, the remaining free parameter, namely
the singlet self coupling $b_4$, is taken to be the one that maximizes
the strength of the phase transition, computed using a modified version
of CosmoTransitions (see https://arxiv.org/abs/1109.4189).''',
                     theory_Tstar=50,
                     theory_gstar=106.75,
                     theory_vw=0.95,
                     theory_Senscurve=0,
                     theory_hasScenarios=False)
        singlet_miki_theory.save()

        miki_points = np.genfromtxt(os.path.join(filedir, 'miki_singlet_portal.txt'), delimiter=' ',names=True)
        Tn = miki_points['Tstar']
        alpha_n = miki_points['alpha']
        beta_H_n = miki_points['betaoverH']
        m = miki_points['m']
        a2 = miki_points['a2']
        
        for i, (this_m, this_a2, this_Tn, this_alpha_n, this_beta_H_n) in \
            enumerate(zip(m, a2, Tn, alpha_n, beta_H_n)):
            point = ParameterChoice(theory=singlet_miki_theory,
                                    number=(i+1),
                                 point_longlabel='$m = %d\, \mathrm{GeV}, \, a_2 = %g$' % (this_m, this_a2),
                                 Tstar=this_Tn,
                                 alpha=this_alpha_n,
                                 BetaoverH=this_beta_H_n)

            point.save()



            



        singletscalars_moritz_theory = \
            Theory(theory_name=r'Singlet scalar benchmark points (Breitbach et al.)',
                                  theory_description='''Benchmark points for a model with two gauge singlet scalars in a hidden sector.''',
                   theory_notes=r'''The underlying random parameter scan contains 1000 points. Note that not all of these points fall into the plotted regions. The Lagrangian as well as the parameter regions used for the scatter plots are given in Section III of https://arxiv.org/abs/1811.11175''',
                   theory_Tstar=100,
                   theory_gstar=106.75,
                   theory_vw=0.95,
                   theory_Senscurve=0,
                   theory_hasScenarios=False)
        singletscalars_moritz_theory.save()

        moritz_points = np.genfromtxt(os.path.join(filedir, 'datapoints_TwoRealScalarSinglets.csv'), delimiter=',',names=True)
        scale=200
        Tn = moritz_points['T_nuc']*scale
        alpha_n = np.abs(moritz_points['alpha'])
        beta_H_n = moritz_points['beta_per_H']
        gstar = moritz_points['rel_dof']

        for i, (this_Tn, this_alpha_n, this_beta_H_n, this_gstar) in \
            enumerate(zip(Tn, alpha_n, beta_H_n, gstar)):
            point = ParameterChoice(theory=singletscalars_moritz_theory,
                                    number=(i+1),
                                    point_longlabel='Point %d' % (i+1),
                                    Tstar=this_Tn,
                                    alpha=this_alpha_n,
                                    BetaoverH=this_beta_H_n,
                                    gstar=this_gstar)

            point.save()



        darkphoton_moritz_theory = \
            Theory(theory_name=r'Dark photon benchmark points (Breitbach et al.)',
                                  theory_description='''Benchmark points for a model with a spontaneously broken $\mathrm{U}(1)$ gauge symmetry in a hidden sector.''',
                   theory_notes=r'''The underlying random parameter scan contains 1000 points. Note that not all of these points fall into the plotted regions. The Lagrangian as well as the parameter regions used for the scatter plots are given in Section III of https://arxiv.org/abs/1811.11175''',
                   theory_Tstar=50,
                   theory_gstar=106.75,
                   theory_vw=0.95,
                   theory_Senscurve=0,
                   theory_hasScenarios=False)
        darkphoton_moritz_theory.save()

        moritz_points = np.genfromtxt(os.path.join(filedir, 'datapoints_DarkPhoton.csv'), delimiter=',',names=True)
        scale=200
        Tn = moritz_points['T_nuc']*scale
        alpha_n = moritz_points['alpha']
        beta_H_n = moritz_points['beta_per_H']
        gstar = moritz_points['rel_dof']

        
        for i, (this_Tn, this_alpha_n, this_beta_H_n, this_gstar) in \
            enumerate(zip(Tn, alpha_n, beta_H_n, gstar)):
            point = ParameterChoice(theory=darkphoton_moritz_theory,
                                    number=(i+1),
                                    point_longlabel='Point %d' % (i+1),
                                    Tstar=this_Tn,
                                    alpha=this_alpha_n,
                                    BetaoverH=this_beta_H_n,
                                    gstar=this_gstar)

            point.save()


        gaugedlepton_madge_theory = \
            Theory(theory_name=r'Gauged Lepton Number Model benchmark points',
                                  theory_description='''Lepton number breaking phase transition in an extension of the SM with gauged lepton number''',
                   theory_notes=r'''Benchmark points for the lepton number phase transition in the
model considered in https://arxiv.org/abs/1809.09110, see section 5.2
for the potential.  Lepton number is gauged as a $U(1)_\ell$ gauge
group. The corresponding gauge boson acquires a mass $m_{Z'}$ when
$U(1)_\ell$ is spontaneously broken by an SM singlet scalar $\phi$
with mass $m_\phi$ and lepton number 3. The VEV is set to $v_\phi =
2\,\text{TeV}$. Four different scenarios for the masses of the DM
($m_\text{DM}$) and additional leptons ($m_\text{HL}$) are
considered.''',
                   theory_Tstar=500,
                   theory_gstar=130,
                   theory_vw=1.0,
                   theory_Senscurve=0,
                   theory_hasScenarios=True)
        gaugedlepton_madge_theory.save()

        madge_points = np.genfromtxt(os.path.join(filedir, 'BenchmarksGaugedLeptonNumber.csv'), delimiter=',',names=True,dtype=None,encoding=None)
        Tn = madge_points['Tn']
        alpha_n = madge_points['alpha']
        beta_H_n = madge_points['betaoverH']
        gstar = madge_points['gstar']
        label = madge_points['label']


        gaugedlepton_madge_scenario_A = \
            Scenario(scenario_theory=gaugedlepton_madge_theory,
                     scenario_number=1,
                     scenario_name="Scenario A",
                     scenario_description=r'$m_\text{DM} = 0$, $m_\text{HL} = 0$')
        gaugedlepton_madge_scenario_A.save()
        
        gaugedlepton_madge_scenario_B = \
            Scenario(scenario_theory=gaugedlepton_madge_theory,
                     scenario_number=2,
                     scenario_name="Scenario B",
                     scenario_description=r'$m_\text{DM} = 200\,\text{GeV}$, $m_\text{HL} = 210\,\text{GeV}$ ')
        gaugedlepton_madge_scenario_B.save()

        gaugedlepton_madge_scenario_C = \
            Scenario(scenario_theory=gaugedlepton_madge_theory,
                     scenario_number=3,
                     scenario_name="Scenario C",
                     scenario_description=r'$m_\text{DM} = 500\,\text{GeV}$, $m_\text{HL} = 1\,\text{TeV}$')
        gaugedlepton_madge_scenario_C.save()
        
        gaugedlepton_madge_scenario_D = \
            Scenario(scenario_theory=gaugedlepton_madge_theory,
                     scenario_number=4,
                     scenario_name="Scenario D",
                     scenario_description=r'$h^2\Omega_\text{DM} = 0.12$, $m_\text{HL} = 1.5\,m_\text{DM}$')
        gaugedlepton_madge_scenario_D.save()

        
        
        for i, (this_Tn, this_alpha_n, this_beta_H_n, this_gstar, this_label) in \
            enumerate(zip(Tn, alpha_n, beta_H_n, gstar, label)):

            letter, mphi, mz = this_label.split('_')

            letter = letter.strip()
            labelstring = r"%s: $(m_\phi, m_{Z'}) = (%d,%d)\, \mathrm{GeV}$" % (letter, int(mphi), int(mz))

            if letter == 'A':
                this_scenario=gaugedlepton_madge_scenario_A
            elif letter == 'B':
                this_scenario=gaugedlepton_madge_scenario_B
            elif letter == 'C':
                this_scenario=gaugedlepton_madge_scenario_C
            elif letter == 'D':
                this_scenario=gaugedlepton_madge_scenario_D
            else:
                raise Exception('Unknown gauged lepton scenario')
                
            point = ParameterChoice(theory=gaugedlepton_madge_theory,
                                    number=(i+1),
                                    point_longlabel=labelstring,
                                    Tstar=this_Tn,
                                    alpha=this_alpha_n,
                                    BetaoverH=this_beta_H_n,
                                    gstar=this_gstar,
                                    scenario=this_scenario)

            point.save()

            



        composite_theory \
            = Theory(theory_name=r'Composite Higgs models benchmark points',
                                  theory_description=r'''description goes here''',
                    theory_notes=r'''notes go here''',
                     theory_Tstar=150,
                     theory_gstar=106.75,
                     theory_vw=0.95,
                     theory_Senscurve=0,
                     theory_hasScenarios=False)
        composite_theory.save()

        
        pA = ParameterChoice(theory=composite_theory,
                             number=1,
                             point_shortlabel=r'M1',
                             point_longlabel=r'Meson-like $m_\chi=600\, \mathrm{GeV}; \, N=5.4$',
                             Tstar=153.5,
                             alpha=3.69994,
                             BetaoverH=274.654)

        pA.save()
        
        pB = ParameterChoice(theory=composite_theory,
                             number=2,
                             point_shortlabel=r'M2',
                             point_longlabel=r'Meson-like $m_\chi=700\, \mathrm{GeV}; \, N=3$',
                             Tstar=191.881,
                             alpha=0.730951,
                             BetaoverH=507.016)

        pB.save()


        pC = ParameterChoice(theory=composite_theory,
                             number=3,
                             point_shortlabel=r'G1',
                             point_longlabel=r'Glueball-like $m_\chi=200\, \mathrm{GeV}; \, N=6.6$',
                             Tstar=134.035,
                             alpha=392893,
                             BetaoverH=82.7087)

        pC.save()
        
        pD = ParameterChoice(theory=composite_theory,
                             number=4,
                             point_shortlabel=r'G2',
                             point_longlabel=r'Glueball-like $m_\chi=200\, \mathrm{GeV}; \, N=5.4$',
                             Tstar=128.961,
                             alpha=9454.681,
                             BetaoverH=150.123)

        pD.save()

        pE = ParameterChoice(theory=composite_theory,
                             number=5,
                             point_shortlabel=r'G3',
                             point_longlabel=r'Glueball-like $m_\chi=300\, \mathrm{GeV}; \, N=4.2$',
                             Tstar=147.908,
                             alpha=597.929,
                             BetaoverH=184.682)

        pE.save()
        
        pF = ParameterChoice(theory=composite_theory,
                             number=6,
                             point_shortlabel=r'G4',
                             point_longlabel=r'Glueball-like $m_\chi=1000\, \mathrm{GeV}; \, N=4.2$',
                             Tstar=272.358,
                             alpha=6.62143,
                             BetaoverH=176.709)

        pF.save()



        
        

        eft_miki_theory = \
            Theory(theory_name=r'EFT benchmark points',
                   theory_description=r''' Benchmark points for the SM extended with effective operators up to dimension eight.''',
                   theory_notes=r'''The new physics potential reads
                   $$\Delta V = \frac{c_6}{f^2}|H|^6 + \frac{c_8}{f^4}|H|^8.$$
                   The effective scale $f/\sqrt{c}$ below is defined by $c/f^2 \equiv \frac{c_6}{f^2} + \frac{3}{2} v^2 \frac{c_8}{f^4}$. The nucleation temperature and other parameters relevant for the 
gravitational wave spectrum have very
little dependence on $c_6$ and $c_8$ independently (see https://arxiv.org/abs/1802.02168); and 
they have been computed using
a modified version of CosmoTransitions (see https://arxiv.org/abs/1109.4189).''',
                   theory_Tstar=100,
                   theory_gstar=106.75,
                   theory_vw=0.95,
                   theory_Senscurve=0,
                   theory_hasScenarios=True)
        eft_miki_theory.save()

        eft_miki_scenario_A = \
            Scenario(scenario_theory=eft_miki_theory,
                     scenario_number=1,
                     scenario_name="Scenario A",
                     scenario_Tstar=50,
                     scenario_description=r'$T_{\rm n} = 50\, \text{GeV}$')
        eft_miki_scenario_A.save()

        eft_miki_scenario_B = \
            Scenario(scenario_theory=eft_miki_theory,
                     scenario_number=2,
                     scenario_name="Scenario B",
                     scenario_Tstar=100,
                     scenario_description=r'$T_{\rm n} = 100\, \text{GeV}$')
        eft_miki_scenario_B.save()


        


        eft_points_A = np.genfromtxt(os.path.join(filedir, 'forDavidTn50.txt'), delimiter=' ',names=True)
        effscale = eft_points_A['effscale']
        alpha_n = eft_points_A['alpha']
        beta_H_n = eft_points_A['betaoverH']

        for i, (this_effscale, this_Tn, this_alpha_n, this_beta_H_n) in \
            enumerate(zip(effscale, Tn, alpha_n, beta_H_n)):
            
            point = ParameterChoice(theory=eft_miki_theory,
                                    number=(i+1),
                                    point_longlabel=r'$f/\sqrt{c} = %.2f \, \text{GeV}$' % this_effscale,
                                    Tstar=50,
                                    alpha=this_alpha_n,
                                    BetaoverH=this_beta_H_n,
                                    gstar=106.75,
                                    scenario=eft_miki_scenario_A)

            point.save()

        eft_points_B = np.genfromtxt(os.path.join(filedir, 'forDavidTn100.txt'), delimiter=' ',names=True)
        effscale = eft_points_B['effscale']
        alpha_n = eft_points_B['alpha']
        beta_H_n = eft_points_B['betaoverH']
        
        
        for i, (this_effscale, this_Tn, this_alpha_n, this_beta_H_n) in \
            enumerate(zip(effscale, Tn, alpha_n, beta_H_n)):
            
            point = ParameterChoice(theory=eft_miki_theory,
                                    number=(i+1),
                                    point_longlabel=r'$f/\sqrt{c} = %.2f \, \text{GeV}$' % this_effscale,
                                    Tstar=100,
                                    alpha=this_alpha_n,
                                    BetaoverH=this_beta_H_n,
                                    gstar=106.75,
                                    scenario=eft_miki_scenario_B)

            point.save()

        susy_theory \
            = Theory(theory_name=r'SUSY model benchmark points',
                                  theory_description=r'''description goes here''',
                    theory_notes=r'''notes go here''',
                     theory_Tstar=100,
                     theory_gstar=108.75,
                     theory_vw=0.95,
                     theory_Senscurve=0,
                     theory_hasScenarios=True)
        susy_theory.save()

        susy_scenario_1 = \
            Scenario(scenario_theory=susy_theory,
                     scenario_number=1,
                     scenario_name="Scenario 1",
                     scenario_Tstar=100,
                     scenario_description=r'(this scenario has 2 benchmark points)')
        susy_scenario_1.save()
                
        p1_A = ParameterChoice(theory=susy_theory,
                               number=1,
                               point_shortlabel=r'1A',
                               point_longlabel=r'SUSY 1 point A',
                               Tstar=112,
                               alpha=0.037,
                               BetaoverH=277,
                               scenario=susy_scenario_1)

        p1_A.save()

        p1_B = ParameterChoice(theory=susy_theory,
                               number=2,
                               point_shortlabel=r'1B',
                               point_longlabel=r'SUSY 1 point B',
                               Tstar=76.4,
                               alpha=0.143,
                               BetaoverH=6.0,
                               scenario=susy_scenario_1)

        p1_B.save()


        susy_scenario_2 = \
            Scenario(scenario_theory=susy_theory,
                     scenario_number=2,
                     scenario_name="Scenario 2",
                     scenario_Tstar=140,
                     scenario_description=r'(this scenario has 2 benchmark points)')
        susy_scenario_2.save()
                
        p2_A = ParameterChoice(theory=susy_theory,
                               number=3,
                               point_shortlabel=r'2A',
                               point_longlabel=r'SUSY 2 point A',
                               Tstar=135,
                               alpha=0.050,
                               BetaoverH=830,
                               vw=0.73,
                               scenario=susy_scenario_2)

        p2_A.save()

        p2_B = ParameterChoice(theory=susy_theory,
                               number=4,
                               point_shortlabel=r'2B',
                               point_longlabel=r'SUSY 2 point B',
                               Tstar=146,
                               alpha=0.040,
                               BetaoverH=2914,
                               vw=0.72,
                               scenario=susy_scenario_2)

        p2_B.save()


        susy_scenario_3 = \
            Scenario(scenario_theory=susy_theory,
                     scenario_number=3,
                     scenario_name="Scenario 3",
                     scenario_Tstar=75,
                     scenario_description=r'(this scenario has 4 benchmark points)')
        susy_scenario_3.save()
                
        p3_A = ParameterChoice(theory=susy_theory,
                               number=5,
                               point_shortlabel=r'3A',
                               point_longlabel=r'SUSY 3 point A',
                               Tstar=74,
                               alpha=0.062,
                               BetaoverH=214,
                               vw=0.1,
                               scenario=susy_scenario_3)

        p3_A.save()

        p3_B = ParameterChoice(theory=susy_theory,
                               number=6,
                               point_shortlabel=r'3B',
                               point_longlabel=r'SUSY 3 point B',
                               Tstar=74,
                               alpha=0.062,
                               BetaoverH=214,
                               vw=0.5,
                               scenario=susy_scenario_3)

        p3_B.save()

        p3_C = ParameterChoice(theory=susy_theory,
                               number=7,
                               point_shortlabel=r'3C',
                               point_longlabel=r'SUSY 3 point C',
                               Tstar=79,
                               alpha=0.045,
                               BetaoverH=200,
                               vw=0.1,
                               scenario=susy_scenario_3)

        p3_C.save()

        p3_D = ParameterChoice(theory=susy_theory,
                               number=8,
                               point_shortlabel=r'3D',
                               point_longlabel=r'SUSY 3 point D',
                               Tstar=79,
                               alpha=0.045,
                               BetaoverH=200,
                               vw=0.5,
                               scenario=susy_scenario_3)

        p3_D.save()
        
        
        susy_scenario_4 = \
            Scenario(scenario_theory=susy_theory,
                     scenario_number=4,
                     scenario_name="Scenario 4",
                     scenario_Tstar=100,
                     scenario_description=r'(this scenario has 1 benchmark points)')
        susy_scenario_4.save()
                
        p4_A = ParameterChoice(theory=susy_theory,
                               number=5,
                               point_shortlabel=r'4A',
                               point_longlabel=r'SUSY 4 point A',
                               Tstar=48,
                               alpha=0.22,
                               BetaoverH=57,
                               vw=0.95,
                               scenario=susy_scenario_4)

        p4_A.save()

            
        
            
        print('done populating.')
        print('NOTE: run python3 manage.py flush to clear tables')

        
    def handle(self, *args, **options):
        self._populate_db()
