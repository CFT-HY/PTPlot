from django.core.management.base import BaseCommand
from ptplot.models import *

import numpy as np

import os, string, math

filedir = os.path.dirname(os.path.realpath(__file__))


class Command(BaseCommand):
    args = '<foo bar ...>'
    help = 'our help string comes here'

    def _populate_db(self):
        print('populating DB...')
        
#         singlet_model \
#             = Model(model_name=r'Singlet (Higgs Portal) benchmark points',
#                                   model_description=r''' 
# Real singlet extension of the Standard Model with $Z_2$
# symmetry, with $m_S = 250\, \mathrm{GeV}$.''',
#                     model_notes=r'''Benchmark points from https://arxiv.org/abs/1512.06239. Data
# from Table 3, see potential, Eq. (30), for details of potential
# parameters $(a_2,b_4)$. $T_*$ is taken to be $50\, \mathrm{GeV}$ for the plot.
#                                 ''',
#                      model_Tstar=50,
#                      model_gstar=106.75,
#                      model_vw=0.95,
#                      model_Senscurve=0,
#                      model_hasScenarios=False)
#         singlet_model.save()

        
#         pA = ParameterChoice(model=singlet_model,
#                              number=1,
#                              point_shortlabel=r'A',
#                              point_longlabel=r'$(a_2,b_4) = (2.8,2.1)$',
#                              Tstar=70.6,
#                              alpha=0.09,
#                              BetaoverH=47.35)

#         pA.save()
        
#         pB = ParameterChoice(model=singlet_model,
#                              number=2,
#                              point_shortlabel=r'B',
#                              point_longlabel=r'$(a_2,b_4) = (2.9,2.6)$',
#                              Tstar=65.2,
#                              alpha=0.12,
#                              BetaoverH=29.96)

#         pB.save()
        
        
#         pC = ParameterChoice(model=singlet_model,
#                              number=3,
#                              point_shortlabel=r'C',
#                              point_longlabel=r'$(a_2,b_4) = (3.0,3.3)$',                          
#                              Tstar=49.6,
#                              alpha=0.17,
#                              BetaoverH=12.54)

#         pC.save()

#         pD = ParameterChoice(model=singlet_model,
#                              number=4,
#                              point_shortlabel=r'D',
#                              point_longlabel=r'$(a_2,b_4) = (3.1,4.0)$',
#                              Tstar=56.4,
#                              alpha=0.20,
#                              BetaoverH=6.42)

#         pD.save()





        twohdm_josemi_model = \
            Model(model_name=r'2HDM benchmark points',
                                  model_description='''Benchmark points for the two-Higgs-doublet model with a softly-broken $Z_2$ symmetry (supplied by G. Dorsch and J.M. No).''',
                   model_notes=r'''
Benchmark points for the two-Higgs-doublet model (2HDM) with a softly-broken $Z_{2}$ symmetry, with scalar potential
\begin{eqnarray}
V(H_1,H_2) & = & \mu^2_1 \left|H_1\right|^2 + \mu^2_2\left|H_2\right|^2 - \mu^2 \left[H_1^{\dagger}H_2+\mathrm{h.c.}\right] +\frac{\lambda_1}{2}\left|H_1\right|^4 
+\frac{\lambda_2}{2}\left|H_2\right|^4 \nonumber \\
&  & + \lambda_3 \left|H_1\right|^2\left|H_2\right|^2 +\lambda_4 \left|H_1^{\dagger}H_2\right|^2 +
 \frac{\lambda_5}{2}\left[\left(H_1^{\dagger}H_2\right)^2+\mathrm{h.c.}\right] \, , \nonumber
\end{eqnarray}
In the mass basis, there are three new physical states in addition to the 125 GeV Higgs $h$: 
a charged scalar $H^{\pm}$ and two neutral states $H_0$, $A_0$. Apart from their masses, the 2HDM features as free 
parameters two angles ($\beta$ and $\alpha$) and $\mu^2$. In the following results we consider $m_{H^{\pm}} = m_{A_0}$, 
$\mathrm{cos} (\beta - \alpha) = 0$ (the 2HDM alignment limit) an fix for convenience $\mu^2 (\mathrm{tan} \beta + \mathrm{tan}^{-1} \beta) = m_{H_0}^2$.
Results are shown for benchmarks in $m_{H_0} \in [180\,\mathrm{GeV},\,\,450\,\mathrm{GeV}]$ and 
$m_{A_0} \in [m_{H_0}+ 150\,\mathrm{GeV} ,\,\,m_{H_0} + 350\,\mathrm{GeV}]$.
''',
                   model_Tstar=50,
                   model_gstar=106.75,
                   model_vw=0.7,
                   model_MissionProfile=0,
                   model_hasScenarios=True)
        twohdm_josemi_model.save()

        josemi_set_1 = \
            Scenario(scenario_model=twohdm_josemi_model,
                     scenario_number=1,
                     scenario_name="Set 1",
                     scenario_description=r'2HDM points which are currently allowed both for Type I and Type II 2HDM. For Type II, these will be probed by the LHC in the future, while for Type I the LHC will not be able to exclude these benchmarks, depending on the value of $\tan\beta$ (which does not influence the strength of the PT).')
        josemi_set_1.save()
        
        josemi_points = np.genfromtxt(os.path.join(filedir, 'josemi_2hdm.txt'), delimiter=',',names=True)
        Tn = josemi_points['Tn']
        alpha_n = josemi_points['alpha_n']
        beta_H_n = josemi_points['beta_H_n']
        tanb = josemi_points['tanb']
        mH = josemi_points['mH']
        mA = josemi_points['mA']

        first_set_point_count = 0
        
        for i, (this_mH, this_mA, this_Tn, this_alpha_n, this_beta_H_n, this_tanb) in \
            enumerate(zip(mH, mA, Tn, alpha_n, beta_H_n, tanb)):
            point = ParameterChoice(model=twohdm_josemi_model,
                                    number=(i+1),
                                    point_longlabel=r'$(m_H,m_A) = (%d,%d) \, \mathrm{GeV}$, $\tan \beta = %d$' % (this_mH, this_mA, this_tanb),
                                    Tstar=this_Tn,
                                    alpha=this_alpha_n,
                                    BetaoverH=this_beta_H_n,
                                    scenario=josemi_set_1)

            point.save()

            first_set_point_count += 1


        josemi_set_2 = \
            Scenario(scenario_model=twohdm_josemi_model,
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
            point = ParameterChoice(model=twohdm_josemi_model,
                                    number=(first_set_point_count + i+1),
                                    point_longlabel=r'$(m_H,m_A) = (%d,%d) \, \mathrm{GeV}$, $\tan \beta = %d$' % (this_mH, this_mA, this_tanb),
                                    Tstar=this_Tn,
                                    alpha=this_alpha_n,
                                    BetaoverH=this_beta_H_n,
                                    scenario=josemi_set_2)

            point.save()

            

#         singlet_miki_model = \
#             Model(model_name=r'$Z_2$-symmetric singlet scalar benchmark points',
#                                   model_description=r'''Benchmark points for the SM extended with a scalar singlet with
# $Z_2$ symmetry (supplied by M. Chala).''',
#                     model_notes=r'''The new physics potential reads

# $$\Delta V = \frac{1}{2}a_2 |H|^2 S^2 + \frac{1}{2} b_2 S^2 + \frac{1}{4} 
# b_4 S^4.$$

# The parameter $m$ below stands for the physical mass of the singlet.
# For each pair $(m, a_2)$, the remaining free parameter, namely
# the singlet self coupling $b_4$, is taken to be the one that maximizes
# the strength of the phase transition, computed using a modified version
# of CosmoTransitions (see https://arxiv.org/abs/1109.4189).''',
#                      model_Tstar=50,
#                      model_gstar=106.75,
#                      model_vw=1.0,
#                      model_MissionProfile=0,
#                      model_hasScenarios=False)
#         singlet_miki_model.save()

#         miki_points = np.genfromtxt(os.path.join(filedir, 'miki_singlet_portal.txt'), delimiter=' ',names=True)
#         Tn = miki_points['Tstar']
#         alpha_n = miki_points['alpha']
#         beta_H_n = miki_points['betaoverH']
#         m = miki_points['m']
#         a2 = miki_points['a2']
        
#         for i, (this_m, this_a2, this_Tn, this_alpha_n, this_beta_H_n) in \
#             enumerate(zip(m, a2, Tn, alpha_n, beta_H_n)):
#             point = ParameterChoice(model=singlet_miki_model,
#                                     number=(i+1),
#                                  point_longlabel='$m = %d\, \mathrm{GeV}, \, a_2 = %g$' % (this_m, this_a2),
#                                  Tstar=this_Tn,
#                                  alpha=this_alpha_n,
#                                  BetaoverH=this_beta_H_n)

#             point.save()


        singlet_jonathan_z2_model = \
            Model(model_name=r'$Z_2$-symmetric singlet scalar benchmark points',
                                  model_description=r'''Benchmark points for the SM extended with a scalar singlet with
$Z_2$ symmetry (supplied by J. Kozaczuk).''',
                    model_notes=r'''The new physics potential reads

$$\Delta V = \frac{1}{2}a_2 |H|^2 S^2 + \frac{1}{2} b_2 S^2 + \frac{1}{4} 
b_4 S^4.$$

The parameter $m$ below stands for the physical mass of the singlet.
For each pair $(m, a_2)$, the remaining free parameter, namely
the singlet self coupling $b_4$, is taken to be the one that maximizes
the strength of the phase transition, computed using a modified version
of CosmoTransitions (see https://arxiv.org/abs/1109.4189).''',
                     model_Tstar=50,
                     model_gstar=106.75,
                     model_vw=1.0,
                     model_MissionProfile=0,
                     model_hasScenarios=False)
        singlet_jonathan_z2_model.save()

        jonathan_z2_points = np.genfromtxt(os.path.join(filedir, 'GW_singlet_Z2.dat'), delimiter=',',names=True)
        Tn = jonathan_z2_points['Tstar']
        alpha_n = jonathan_z2_points['alpha']
        beta_H_n = jonathan_z2_points['betaoverH']
        m = jonathan_z2_points['m']
        a2 = jonathan_z2_points['a2']
        
        for i, (this_m, this_a2, this_Tn, this_alpha_n, this_beta_H_n) in \
            enumerate(zip(m, a2, Tn, alpha_n, beta_H_n)):
            point = ParameterChoice(model=singlet_jonathan_z2_model,
                                    number=(i+1),
                                 point_longlabel='$m = %d\, \mathrm{GeV}, \, a_2 = %g$' % (this_m, this_a2),
                                 Tstar=this_Tn,
                                 alpha=this_alpha_n,
                                 BetaoverH=this_beta_H_n)

            point.save()
            


            



        singletscalars_moritz_model = \
            Model(model_name=r'Scalar dark sector benchmark points',
                                  model_description='''Benchmark points for a model with two gauge singlet scalars in a hidden sector (supplied by M. Breitbach).''',
                   model_notes=r'''The underlying random parameter scan contains 1000 points. Note that not all of these points fall into the plotted regions. The Lagrangian as well as the parameter regions used for the scatter plots are given in Section III of https://arxiv.org/abs/1811.11175''',
                   model_Tstar=100,
                   model_gstar=106.75,
                   model_vw=0.95,
                   model_MissionProfile=0,
                   model_hasScenarios=False)
        singletscalars_moritz_model.save()

        moritz_points = np.genfromtxt(os.path.join(filedir, 'datapoints_TwoRealScalarSinglets.csv'), delimiter=',',names=True)
        scale=200
        Tn = moritz_points['T_nuc']*scale
        alpha_n = np.abs(moritz_points['alpha'])
        beta_H_n = moritz_points['beta_per_H']
        gstar = moritz_points['rel_dof']

        for i, (this_Tn, this_alpha_n, this_beta_H_n, this_gstar) in \
            enumerate(zip(Tn, alpha_n, beta_H_n, gstar)):
            point = ParameterChoice(model=singletscalars_moritz_model,
                                    number=(i+1),
                                    point_longlabel='Point %d' % (i+1),
                                    Tstar=this_Tn,
                                    alpha=this_alpha_n,
                                    BetaoverH=this_beta_H_n,
                                    gstar=this_gstar)

            point.save()



        darkphoton_moritz_model = \
            Model(model_name=r'Dark photon benchmark points)',
                                  model_description='''Benchmark points for a model with a spontaneously broken $\mathrm{U}(1)$ gauge symmetry in a hidden sector (supplied by M. Breitbach).''',
                   model_notes=r'''The underlying random parameter scan contains 1000 points. Note that not all of these points fall into the plotted regions. The Lagrangian as well as the parameter regions used for the scatter plots are given in Section III of https://arxiv.org/abs/1811.11175''',
                   model_Tstar=50,
                   model_gstar=106.75,
                   model_vw=0.95,
                   model_MissionProfile=0,
                   model_hasScenarios=False)
        darkphoton_moritz_model.save()

        moritz_points = np.genfromtxt(os.path.join(filedir, 'datapoints_DarkPhoton.csv'), delimiter=',',names=True)
        scale=200
        Tn = moritz_points['T_nuc']*scale
        alpha_n = moritz_points['alpha']
        beta_H_n = moritz_points['beta_per_H']
        gstar = moritz_points['rel_dof']

        
        for i, (this_Tn, this_alpha_n, this_beta_H_n, this_gstar) in \
            enumerate(zip(Tn, alpha_n, beta_H_n, gstar)):
            point = ParameterChoice(model=darkphoton_moritz_model,
                                    number=(i+1),
                                    point_longlabel='Point %d' % (i+1),
                                    Tstar=this_Tn,
                                    alpha=this_alpha_n,
                                    BetaoverH=this_beta_H_n,
                                    gstar=this_gstar)

            point.save()


        gaugedlepton_madge_model = \
            Model(model_name=r'Gauged Lepton Number Model benchmark points',
                                  model_description='''Lepton number breaking phase transition in an extension of the SM with gauged lepton number (supplied by E. Madge).''',
                   model_notes=r'''Benchmark points for the lepton number phase transition in the
model considered in https://arxiv.org/abs/1809.09110, see section 5.2
for the potential.  Lepton number is gauged as a $U(1)_\ell$ gauge
group. The corresponding gauge boson acquires a mass $m_{Z'}$ when
$U(1)_\ell$ is spontaneously broken by an SM singlet scalar $\phi$
with mass $m_\phi$ and lepton number 3. The VEV is set to $v_\phi =
2\,\text{TeV}$. Four different scenarios for the masses of the DM
($m_\text{DM}$) and additional leptons ($m_\text{HL}$) are
considered.''',
                   model_Tstar=500,
                   model_gstar=130,
                   model_vw=1.0,
                   model_MissionProfile=0,
                   model_hasScenarios=True)
        gaugedlepton_madge_model.save()

        madge_points = np.genfromtxt(os.path.join(filedir, 'BenchmarksGaugedLeptonNumber.csv'), delimiter=',',names=True,dtype=None,encoding=None)
        Tn = madge_points['Tn']
        alpha_n = madge_points['alpha']
        beta_H_n = madge_points['betaoverH']
        gstar = madge_points['gstar']
        label = madge_points['label']


        gaugedlepton_madge_scenario_A = \
            Scenario(scenario_model=gaugedlepton_madge_model,
                     scenario_number=1,
                     scenario_name="Scenario A",
                     scenario_description=r'$m_\text{DM} = 0$, $m_\text{HL} = 0$')
        gaugedlepton_madge_scenario_A.save()
        
        gaugedlepton_madge_scenario_B = \
            Scenario(scenario_model=gaugedlepton_madge_model,
                     scenario_number=2,
                     scenario_name="Scenario B",
                     scenario_description=r'$m_\text{DM} = 200\,\text{GeV}$, $m_\text{HL} = 210\,\text{GeV}$ ')
        gaugedlepton_madge_scenario_B.save()

        gaugedlepton_madge_scenario_C = \
            Scenario(scenario_model=gaugedlepton_madge_model,
                     scenario_number=3,
                     scenario_name="Scenario C",
                     scenario_description=r'$m_\text{DM} = 500\,\text{GeV}$, $m_\text{HL} = 1\,\text{TeV}$')
        gaugedlepton_madge_scenario_C.save()
        
        gaugedlepton_madge_scenario_D = \
            Scenario(scenario_model=gaugedlepton_madge_model,
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
                
            point = ParameterChoice(model=gaugedlepton_madge_model,
                                    number=(i+1),
                                    point_longlabel=labelstring,
                                    Tstar=this_Tn,
                                    alpha=this_alpha_n,
                                    BetaoverH=this_beta_H_n,
                                    gstar=this_gstar,
                                    scenario=this_scenario)

            point.save()

            



        composite_model \
            = Model(model_name=r'Composite Higgs models benchmark points',
                                  model_description=r'''Benchmark points for minimal composite Higgs models, featuring a PNGB Higgs and a PNGB dilaton (supplied by G. Servant).''',
                    model_notes=r'''Composite Higgs models, which aim at addressing the hierarchy
problem, are a natural framework for very supercooled EW phase
transitions.  The Lagrangian and the parameter regions are given in
Section III and Section VI respectively of
https://arxiv.org/pdf/1804.07314.pdf, Figure 16 of that paper shows
typical values of $\alpha$ and $\beta/H$.  In this framework, the dynamics
of the EW phase transition is governed by the interplay between the
dilaton and the Higgs fields.  In these models where a very large
number of degrees of freedom become massive during the phase
transition, the friction and the bubble wall velocity have not yet
been computed and v_w is set to 0.95 for illustration.  Benchmark
points correspond to two categories where the dilaton (a composite
particle) is either a meson-like or a glueball-like state.''',
                    model_Tstar=150,
                    model_gstar=106.75,
                    model_vw=0.95,
                    model_MissionProfile=0,
                    model_hasScenarios=False,
                    model_hugeAlpha=True)
        composite_model.save()

        
        pA = ParameterChoice(model=composite_model,
                             number=1,
                             point_shortlabel=r'M1',
                             point_longlabel=r'Meson-like $m_\chi=600\, \mathrm{GeV}; \, N=5.4$',
                             Tstar=153.5,
                             alpha=3.69994,
                             BetaoverH=274.654)

        pA.save()
        
        pB = ParameterChoice(model=composite_model,
                             number=2,
                             point_shortlabel=r'M2',
                             point_longlabel=r'Meson-like $m_\chi=700\, \mathrm{GeV}; \, N=3$',
                             Tstar=191.881,
                             alpha=0.730951,
                             BetaoverH=507.016)

        pB.save()


        pC = ParameterChoice(model=composite_model,
                             number=3,
                             point_shortlabel=r'G1',
                             point_longlabel=r'Glueball-like $m_\chi=200\, \mathrm{GeV}; \, N=6.6$',
                             Tstar=134.035,
                             alpha=392893,
                             BetaoverH=82.7087)

        pC.save()
        
        pD = ParameterChoice(model=composite_model,
                             number=4,
                             point_shortlabel=r'G2',
                             point_longlabel=r'Glueball-like $m_\chi=200\, \mathrm{GeV}; \, N=5.4$',
                             Tstar=128.961,
                             alpha=9454.681,
                             BetaoverH=150.123)

        pD.save()

        pE = ParameterChoice(model=composite_model,
                             number=5,
                             point_shortlabel=r'G3',
                             point_longlabel=r'Glueball-like $m_\chi=300\, \mathrm{GeV}; \, N=4.2$',
                             Tstar=147.908,
                             alpha=597.929,
                             BetaoverH=184.682)

        pE.save()
        
        pF = ParameterChoice(model=composite_model,
                             number=6,
                             point_shortlabel=r'G4',
                             point_longlabel=r'Glueball-like $m_\chi=1000\, \mathrm{GeV}; \, N=4.2$',
                             Tstar=272.358,
                             alpha=6.62143,
                             BetaoverH=176.709)

        pF.save()




        RS_model \
            = Model(model_name=r'Randall-Sundrum model benchmark points',
                                  model_description=r'''Benchmark points for the holographic phase transition in Randall-Sundrum models (supplied by G. Nardini).''',
                    model_notes=r'''notes go here''',
                    model_Tstar=500,
                    model_gstar=106.75,
                    model_vw=0.95,
                    model_MissionProfile=0,
                    model_hasScenarios=False,
                    model_hugeAlpha=True)
        RS_model.save()

        
        pB1 = ParameterChoice(model=RS_model,
                              number=1,
                              point_shortlabel=r'B1',
                              point_longlabel=r'$B_1$',
                              Tstar=1053,
                              alpha=1.60,
                              BetaoverH=math.pow(10,2.36))

        pB1.save()

        pB2 = ParameterChoice(model=RS_model,
                              number=2,
                              point_shortlabel=r'B2',
                              point_longlabel=r'$B_2$',
                              Tstar=821.8,
                              alpha=4.61,
                              BetaoverH=math.pow(10,1.99))

        pB2.save()


        pB3 = ParameterChoice(model=RS_model,
                              number=3,
                              point_shortlabel=r'B3',
                              point_longlabel=r'$B_3$',
                              Tstar=770.4,
                              alpha=7.86,
                              BetaoverH=math.pow(10,1.79))

        pB3.save()


        pB4 = ParameterChoice(model=RS_model,
                              number=4,
                              point_shortlabel=r'B4',
                              point_longlabel=r'$B_4$',
                              Tstar=730.6,
                              alpha=17.1,
                              BetaoverH=math.pow(10,1.48))

        pB4.save()


        pB5 = ParameterChoice(model=RS_model,
                              number=5,
                              point_shortlabel=r'B5',
                              point_longlabel=r'$B_5$',
                              Tstar=694.0,
                              alpha=90.1,
                              BetaoverH=math.pow(10,1.97))

        pB5.save()

        
        pB6 = ParameterChoice(model=RS_model,
                              number=6,
                              point_shortlabel=r'B6',
                              point_longlabel=r'$B_6$',
                              Tstar=694.0,
                              alpha=90.1,
                              BetaoverH=math.pow(10,1.97))

        pB6.save()

        pB7 = ParameterChoice(model=RS_model,
                              number=7,
                              point_shortlabel=r'B7',
                              point_longlabel=r'$B_7$',
                              Tstar=612.0,
                              alpha=1047,
                              BetaoverH=math.pow(10,1.67))

        pB7.save()

        pB8 = ParameterChoice(model=RS_model,
                              number=8,
                              point_shortlabel=r'B8',
                              point_longlabel=r'$B_8$',
                              Tstar=566.4,
                              alpha=4e4,
                              BetaoverH=math.pow(10,1.23))

        pB8.save()

        pB9 = ParameterChoice(model=RS_model,
                              number=9,
                              point_shortlabel=r'B9',
                              point_longlabel=r'$B_9$',
                              Tstar=549.3,
                              alpha=4.1e6,
                              BetaoverH=math.pow(10,0.64))

        pB9.save()

        pB10 = ParameterChoice(model=RS_model,
                               number=10,
                               point_shortlabel=r'B10',
                               point_longlabel=r'$B_{10}$',
                               Tstar=546.8,
                               alpha=3.3e7,
                               BetaoverH=math.pow(10,0.34))

        pB10.save()


        pB11 = ParameterChoice(model=RS_model,
                               number=11,
                               point_shortlabel=r'B11',
                               point_longlabel=r'$B_{11}$',
                               Tstar=545.6,
                               alpha=4.5e8,
                               BetaoverH=math.pow(10,-0.32))

        pB11.save()

        pC1 = ParameterChoice(model=RS_model,
                               number=12,
                               point_shortlabel=r'B11',
                               point_longlabel=r'$B_{11}$',
                               Tstar=578.4,
                               alpha=4.3,
                               BetaoverH=math.pow(10,2.03))

        pC1.save()

        pC2 = ParameterChoice(model=RS_model,
                               number=13,
                               point_shortlabel=r'C2',
                               point_longlabel=r'$C_2$',
                               Tstar=416.2,
                               alpha=5e3,
                               BetaoverH=math.pow(10,1.45))

        pC2.save()

        pD1 = ParameterChoice(model=RS_model,
                              number=14,
                              point_shortlabel=r'D1',
                              point_longlabel=r'$D_1$',
                              Tstar=133.7,
                              alpha=5.0,
                              BetaoverH=math.pow(10,1.05))

        pD1.save()

        pE1 = ParameterChoice(model=RS_model,
                              number=15,
                              point_shortlabel=r'E1',
                              point_longlabel=r'$E_1$',
                              Tstar=567.2,
                              alpha=203,
                              BetaoverH=math.pow(10,1.89))

        pE1.save()

        eft_miki_model = \
            Model(model_name=r'EFT benchmark points',
                   model_description=r''' Benchmark points for the SM extended with effective operators up to dimension eight (supplied by M. Chala).''',
                   model_notes=r'''The new physics potential reads
                   $$\Delta V = \frac{c_6}{f^2}|H|^6 + \frac{c_8}{f^4}|H|^8.$$
                   The effective scale $f/\sqrt{c}$ below is defined by $c/f^2 \equiv \frac{c_6}{f^2} + \frac{3}{2} v^2 \frac{c_8}{f^4}$. The nucleation temperature and other parameters relevant for the 
gravitational wave spectrum have very
little dependence on $c_6$ and $c_8$ independently (see https://arxiv.org/abs/1802.02168); and 
they have been computed using
a modified version of CosmoTransitions (see https://arxiv.org/abs/1109.4189).''',
                   model_Tstar=100,
                   model_gstar=106.75,
                   model_vw=0.95,
                   model_MissionProfile=0,
                   model_hasScenarios=True)
        eft_miki_model.save()

        eft_miki_scenario_A = \
            Scenario(scenario_model=eft_miki_model,
                     scenario_number=1,
                     scenario_name="Scenario A",
                     scenario_Tstar=50,
                     scenario_description=r'$T_{\rm n} = 50\, \text{GeV}$')
        eft_miki_scenario_A.save()

        eft_miki_scenario_B = \
            Scenario(scenario_model=eft_miki_model,
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
            
            point = ParameterChoice(model=eft_miki_model,
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
            
            point = ParameterChoice(model=eft_miki_model,
                                    number=(i+1),
                                    point_longlabel=r'$f/\sqrt{c} = %.2f \, \text{GeV}$' % this_effscale,
                                    Tstar=100,
                                    alpha=this_alpha_n,
                                    BetaoverH=this_beta_H_n,
                                    gstar=106.75,
                                    scenario=eft_miki_scenario_B)

            point.save()

        susy_model \
            = Model(model_name=r'Some SUSY embeddings',
                                  model_description=r'''Benchmark points for some SUSY embeddings with chiral 
supersinglets or supertriplets (supplied by G. Nardini).''',
                    model_notes=r'''The benchmark points  SUSY$_1$ are taken from 
https://arxiv.org/abs/1512.06357, SUSY$_2$ from 
https://arxiv.org/abs/1704.02488,  SUSY$_3$ from 
https://arxiv.org/abs/1712.00087, and SUSY$_4$ from 
https://arxiv.org/abs/1602.01351 . Details on the models can be found in 
the corresponding references.''',
                     model_Tstar=100,
                     model_gstar=108.75,
                     model_vw=0.95,
                     model_MissionProfile=0,
                     model_hasScenarios=True)
        susy_model.save()

        susy_scenario_1 = \
            Scenario(scenario_model=susy_model,
                     scenario_number=1,
                     scenario_name="SUSY$_1$",
                     scenario_Tstar=100,
                     scenario_description=r'(this scenario has 2 benchmark points)')
        susy_scenario_1.save()
                
        p1_A = ParameterChoice(model=susy_model,
                               number=1,
                               point_shortlabel=r'1A',
                               point_longlabel=r'SUSY$_1$ point A',
                               Tstar=112,
                               alpha=0.037,
                               BetaoverH=277,
                               scenario=susy_scenario_1)

        p1_A.save()

        p1_B = ParameterChoice(model=susy_model,
                               number=2,
                               point_shortlabel=r'1B',
                               point_longlabel=r'SUSY$_1$ point B',
                               Tstar=95,
                               alpha=0.066,
                               BetaoverH=106,
                               scenario=susy_scenario_1)

        p1_B.save()

        p1_C = ParameterChoice(model=susy_model,
                               number=3,
                               point_shortlabel=r'1C',
                               point_longlabel=r'SUSY$_1$ point C',
                               Tstar=82,
                               alpha=0.105,
                               BetaoverH=33,
                               scenario=susy_scenario_1)

        p1_C.save()

        
        p1_D = ParameterChoice(model=susy_model,
                               number=4,
                               point_shortlabel=r'1D',
                               point_longlabel=r'SUSY$_1$ point D',
                               Tstar=76.4,
                               alpha=0.143,
                               BetaoverH=6.0,
                               scenario=susy_scenario_1)

        p1_D.save()


        susy_scenario_2 = \
            Scenario(scenario_model=susy_model,
                     scenario_number=2,
                     scenario_name="SUSY$_2$",
                     scenario_Tstar=140,
                     scenario_description=r'(this scenario has 2 benchmark points)')
        susy_scenario_2.save()
                
        p2_A = ParameterChoice(model=susy_model,
                               number=5,
                               point_shortlabel=r'2A',
                               point_longlabel=r'SUSY$_2$ point A',
                               Tstar=135,
                               alpha=0.050,
                               BetaoverH=830,
                               vw=0.73,
                               scenario=susy_scenario_2)

        p2_A.save()

        p2_B = ParameterChoice(model=susy_model,
                               number=6,
                               point_shortlabel=r'2B',
                               point_longlabel=r'SUSY$_2$ point B',
                               Tstar=146,
                               alpha=0.040,
                               BetaoverH=2914,
                               vw=0.72,
                               scenario=susy_scenario_2)

        p2_B.save()


        susy_scenario_3 = \
            Scenario(scenario_model=susy_model,
                     scenario_number=3,
                     scenario_name="SUSY$_3$",
                     scenario_Tstar=75,
                     scenario_description=r'(this scenario has 4 benchmark points)')
        susy_scenario_3.save()
                
        p3_A = ParameterChoice(model=susy_model,
                               number=7,
                               point_shortlabel=r'3A',
                               point_longlabel=r'SUSY$_3$ point A',
                               Tstar=74,
                               alpha=0.062,
                               BetaoverH=214,
                               vw=0.1,
                               scenario=susy_scenario_3)

        p3_A.save()

        p3_B = ParameterChoice(model=susy_model,
                               number=8,
                               point_shortlabel=r'3B',
                               point_longlabel=r'SUSY$_3$ point B',
                               Tstar=74,
                               alpha=0.062,
                               BetaoverH=214,
                               vw=0.5,
                               scenario=susy_scenario_3)

        p3_B.save()

        p3_C = ParameterChoice(model=susy_model,
                               number=9,
                               point_shortlabel=r'3C',
                               point_longlabel=r'SUSY$_3$ point C',
                               Tstar=79,
                               alpha=0.045,
                               BetaoverH=200,
                               vw=0.1,
                               scenario=susy_scenario_3)

        p3_C.save()

        p3_D = ParameterChoice(model=susy_model,
                               number=10,
                               point_shortlabel=r'3D',
                               point_longlabel=r'SUSY$_3$ point D',
                               Tstar=79,
                               alpha=0.045,
                               BetaoverH=200,
                               vw=0.5,
                               scenario=susy_scenario_3)

        p3_D.save()
        
        
        susy_scenario_4 = \
            Scenario(scenario_model=susy_model,
                     scenario_number=4,
                     scenario_name="SUSY$_4$",
                     scenario_Tstar=100,
                     scenario_description=r'(this scenario has 1 benchmark points)')
        susy_scenario_4.save()
                
        p4_A = ParameterChoice(model=susy_model,
                               number=11,
                               point_shortlabel=r'4A',
                               point_longlabel=r'SUSY$_4$ point A',
                               Tstar=48,
                               alpha=0.22,
                               BetaoverH=57,
                               vw=0.95,
                               scenario=susy_scenario_4)

        p4_A.save()

            
        

        singlet_jonathan_model = \
            Model(model_name=r'Singlet scalar benchmark points',
                                  model_description='''
                                  Benchmark points for the SM extended with a general real singlet scalar field, $S$ (supplied by J. Kozaczuk).''',
                   model_notes=r'''
$$
\Delta V = b_1 S +  \frac{1}{2} b_2 S^2 + \frac{1}{2} a_1 S \left| H \right|^2 + \frac{1}{2} a_2 S^2 \left| H \right|^2 + \frac{1}{3} b_3 S^3 + \frac{1}{4} b_4 S^4.
$$

In the mass basis, the mass-ordered eigenstates are $m_{1,2}$. The mixing angle between $S$ and $H$ is denoted as $\theta$. Masses considered are $m_2 = 170,\, 240\, \mathrm{GeV}$. We show results for points with $m_2= 170,\, 240\, \mathrm{GeV}$ and $\sin \theta = 0.1$, which are likely to be probed by direct searches at the high-luminosity LHC with $3\, \mathrm{ab}^{-1}$, and $\sin\theta = 0.01$, which will likely remain undetected at colliders. The various parameters in the potential are scanned over as described in the text. See also JHEP 1708 (2017) 096 [http://arxiv.org/abs/arXiv:1704.05844] for more details. 
''',
                   model_Tstar=50,
                   model_gstar=107.75,
                   model_vw=1.0,
                   model_MissionProfile=0,
                   model_hasScenarios=True)
        singlet_jonathan_model.save()

        jonathan_set_1 = \
            Scenario(scenario_model=singlet_jonathan_model,
                     scenario_number=1,
                     scenario_name="Not probed by HL-LHC",
                     scenario_description=r'Set of points that are not probed by HL-LHC')
        jonathan_set_1.save()

        jonathan_set_2 = \
            Scenario(scenario_model=singlet_jonathan_model,
                     scenario_number=2,
                     scenario_name="Will be probed by HL-LHC",
                     scenario_description=r'Set of points that will be probed by HL-LHC')
        jonathan_set_2.save()

        
#        alpha, beta_over_H, probe = np.genfromtxt(os.path.join(filedir, 'GW_singlet_combined.dat'), delimiter=',', unpack=True)
        jonathan_points = np.genfromtxt(os.path.join(filedir, 'GW_singlet_combined_all_params.dat'), delimiter=',', names=True)
        m2 = jonathan_points['m2']
        sinTheta = jonathan_points['sinTheta']
        a2 = jonathan_points['a2']
        b3 = jonathan_points['b3']
        b4 = jonathan_points['b4']
        alpha = jonathan_points['alpha']
        betaoverH = jonathan_points['betaoverH']
        LHCflag = jonathan_points['LHCflag']
        Tstar = jonathan_points['Tstar']
        
        for i, (this_m2, this_sinTheta, this_a2, this_b3, this_b4, this_alpha, this_beta_over_H, this_probe, this_Tstar) in \
            enumerate(zip(m2, sinTheta, a2, b3, b4, alpha, betaoverH, LHCflag, Tstar)):

            if not this_probe:                
                point = ParameterChoice(model=singlet_jonathan_model,
                                        number=(i+1),
#                                        point_longlabel=r'Point %d' % (i+1),
                                        point_longlabel=r'$m_2 = %d\, \mathrm{GeV}$, $\sin \theta = %g$, $a_2 = %g$, $b_3 = %g$, $b_4  = %g$)' % (this_m2, this_sinTheta, this_a2, this_b3, this_b4),
                                        alpha=this_alpha,
                                        Tstar=this_Tstar,
                                        BetaoverH=this_beta_over_H,
                                        scenario=jonathan_set_1)
            else:
                point = ParameterChoice(model=singlet_jonathan_model,
                                        number=(i+1),
#                                        point_longlabel=r'Point %d' % (i+1),
                                        point_longlabel=r'$m_2 = %d\, \mathrm{GeV}$, $\sin \theta = %g$, $a_2 = %g$, $b_3 = %g$, $b_4  = %g$)' % (this_m2, this_sinTheta, this_a2, this_b3, this_b4),                                        
                                        alpha=this_alpha,
                                        Tstar=this_Tstar,
                                        BetaoverH=this_beta_over_H,
                                        scenario=jonathan_set_2)

            point.save()

        
        print('done populating.')
        print('NOTE: run python3 manage.py flush to clear tables')

        
    def handle(self, *args, **options):
        self._populate_db()
