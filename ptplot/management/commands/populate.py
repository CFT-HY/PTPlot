"""Populate the database with models, scenarios and parameter choices"""

from collections import defaultdict
from inspect import cleandoc
import os

from django.core.management.base import BaseCommand
import numpy as np
from pandas import DataFrame, read_csv

from ptplot.science.mission_profile import DEFAULT_MISSION_PROFILE
from ptplot.models import Model, ParameterChoice, Scenario

FILEDIR: str = os.path.dirname(os.path.realpath(__file__))

# pylint: disable=missing-function-docstring


class Command(BaseCommand):
    """Command to populate the database with models, scenarios and points

    The class has to be named "Command" for Django to find it.
    """
    help = "This command populates the database with models, scenarios and parameter choices."

    @staticmethod
    def composite() -> Model:
        composite = Model(
            name="Composite Higgs models benchmark points",
            slug="composite",
            description=(
                "Benchmark points for minimal composite Higgs models, "
                "featuring a PNGB Higgs and a PNGB dilaton (supplied by G. Servant)."
            ),
            notes=cleandoc(r"""
                Composite Higgs models, which aim at addressing the hierarchy problem,
                are a natural framework for very supercooled EW phase transitions.
                The Lagrangian and the parameter regions are given in Section III and Section VI respectively of
                https://arxiv.org/pdf/1804.07314.pdf,
                Figure 16 of that paper shows typical values of $\alpha$ and $\beta/H$.
                In this framework, the dynamics of the EW phase transition is governed
                by the interplay between the dilaton and the Higgs fields.
                In these models where a very large number of degrees of freedom
                become massive during the phase transition,
                the friction and the bubble wall velocity have not yet been computed
                and v_w is set to 0.95 for illustration.
                Benchmark points correspond to two categories where the dilaton
                (a composite particle) is either a meson-like or a glueball-like state.
                """),
            T_star=150,
            g_star=106.75,
            v_wall=0.95,
            mission_profile=DEFAULT_MISSION_PROFILE,
            has_scenarios=False,
            huge_alpha=True
        )
        composite.save()

        pa = ParameterChoice(
            model=composite,
            number=1,
            short_label="M1",
            long_label=r"Meson-like $m_\chi=600\, \mathrm{GeV}; \, N=5.4$",
            T_star=153.5,
            alpha=3.69994,
            beta_over_H=274.654
        )
        pa.save()

        pb = ParameterChoice(
            model=composite,
            number=2,
            short_label="M2",
            long_label=r"Meson-like $m_\chi=700\, \mathrm{GeV}; \, N=3$",
            T_star=191.881,
            alpha=0.730951,
            beta_over_H=507.016
        )
        pb.save()

        pc = ParameterChoice(
            model=composite,
            number=3,
            short_label="G1",
            long_label=r"Glueball-like $m_\chi=200\, \mathrm{GeV}; \, N=6.6$",
            T_star=134.035,
            alpha=392893,
            beta_over_H=82.7087
        )
        pc.save()

        pd = ParameterChoice(
            model=composite,
            number=4,
            short_label="G2",
            long_label=r"Glueball-like $m_\chi=200\, \mathrm{GeV}; \, N=5.4$",
            T_star=128.961,
            alpha=9454.681,
            beta_over_H=150.123
        )
        pd.save()

        pe = ParameterChoice(
            model=composite,
            number=5,
            short_label="G3",
            long_label=r"Glueball-like $m_\chi=300\, \mathrm{GeV}; \, N=4.2$",
            T_star=147.908,
            alpha=597.929,
            beta_over_H=184.682
        )
        pe.save()

        pf = ParameterChoice(
            model=composite,
            number=6,
            short_label="G4",
            long_label=r"Glueball-like $m_\chi=1000\, \mathrm{GeV}; \, N=4.2$",
            T_star=272.358,
            alpha=6.62143,
            beta_over_H=176.709
        )
        pf.save()

        return composite

    @staticmethod
    def dark_photon_moritz() -> Model:
        dark_photon_moritz = Model(
            name="Dark photon benchmark points",
            slug="dark_photon_moritz",
            description=(
                r"Benchmark points for a model with a spontaneously broken $\mathrm{U}(1)$ gauge symmetry "
                "in a hidden sector (supplied by M. Breitbach)."
            ),
            notes=cleandoc("""
                The underlying random parameter scan contains 1000 points.
                Note that not all of these points fall into the plotted regions.
                The Lagrangian as well as the parameter regions used for the scatter plots are given in Section III of
                https://arxiv.org/abs/1811.11175
                """),
            T_star=50,
            g_star=106.75,
            v_wall=0.95,
            mission_profile=DEFAULT_MISSION_PROFILE,
            has_scenarios=False
        )
        dark_photon_moritz.save()

        points: DataFrame = read_csv(
            os.path.join(FILEDIR, "datapoints_DarkPhoton.csv"),
            sep=",",
            dtype=np.float64,
            engine="c",
        )
        points.T_nuc *= 200  # scale factor
        for row in points.itertuples():
            point = ParameterChoice(
                model=dark_photon_moritz,
                number=row.Index + 1,  # type: ignore
                long_label=f"Point {row.Index + 1:d}",  # type: ignore
                T_star=row.T_nuc,
                alpha=row.alpha,
                beta_over_H=row.beta_per_H,
                g_star=row.rel_dof
            )
            point.save()

        return dark_photon_moritz

    @staticmethod
    def eft_miki() -> Model:
        eft_miki = Model(
            name="EFT benchmark points",
            slug="eft_miki",
            description=(
                "Benchmark points for the SM extended with effective operators up to dimension eight "
                "(supplied by M. Chala). "
            ),
            notes=cleandoc(r"""
                The new physics potential reads
                $$\Delta V = \frac{c_6}{f^2}|H|^6 + \frac{c_8}{f^4}|H|^8.$$
                The effective scale $f/\sqrt{c}$ below is defined by
                $c/f^2 \equiv \frac{c_6}{f^2} + \frac{3}{2} v^2 \frac{c_8}{f^4}$.
                The nucleation temperature and other parameters relevant for the ravitational wave spectrum
                have very little dependence on $c_6$ and $c_8$ independently (see https://arxiv.org/abs/1802.02168);
                and they have been computed using a modified version of CosmoTransitions
                (see https://arxiv.org/abs/1109.4189).
                """),
            T_star=100,
            g_star=106.75,
            v_wall=0.95,
            mission_profile=DEFAULT_MISSION_PROFILE,
            has_scenarios=True
        )
        eft_miki.save()

        scenario_a = Scenario(
            model=eft_miki,
            number=1,
            name="Scenario A",
            T_star=50,
            description=r"$T_{\rm n} = 50\, \text{GeV}$"
        )
        scenario_a.save()

        scenario_b = Scenario(
            model=eft_miki,
            number=2,
            name="Scenario B",
            T_star=100,
            description=r"$T_{\rm n} = 100\, \text{GeV}$"
        )
        scenario_b.save()

        points_a: DataFrame = read_csv(
            os.path.join(FILEDIR, "forDavidTn50.txt"),
            sep=" ",
            dtype=np.float64,
            engine="c",
            comment="#",
        )
        first_set_point_count = len(points_a.index)
        for row in points_a.itertuples():
            point = ParameterChoice(
                model=eft_miki,
                number=row.Index + 1,  # type: ignore
                long_label=rf"$f/\sqrt{{c}} = {row.effscale:.2f} \, \text{{GeV}}$",
                T_star=50,
                alpha=row.alpha,
                beta_over_H=row.betaoverH,
                g_star=106.75,
                scenario=scenario_a
            )
            point.save()

        points_b: DataFrame = read_csv(
            os.path.join(FILEDIR, "forDavidTn100.txt"),
            sep=" ",
            dtype=np.float64,
            engine="c",
            comment="#",
        )
        for row in points_b.itertuples():
            point = ParameterChoice(
                model=eft_miki,
                number=first_set_point_count + row.Index + 1,  # type: ignore
                long_label=rf"$f/\sqrt{{c}} = {row.effscale:.2f} \, \text{{GeV}}$",
                T_star=100,
                alpha=row.alpha,
                beta_over_H=row.betaoverH,
                g_star=106.75,
                scenario=scenario_b
            )
            point.save()

        return eft_miki

    @staticmethod
    def gauged_lepton_madge() -> Model:
        gauged_lepton_madge = Model(
            name="Gauged Lepton Number Model benchmark points",
            slug="gauged_lepton_madge",
            description=(
                "Lepton number breaking phase transition in an extension of the SM with gauged lepton number "
                "(supplied by E. Madge)."
            ),
            notes=cleandoc(r"""
                Benchmark points for the lepton number phase transition
                in the model considered in https://arxiv.org/abs/1809.09110,
                see section 5.2 for the potential.
                Lepton number is gauged as a $U(1)_\ell$ gauge group.
                The corresponding gauge boson acquires a mass $m_{Z'}$
                when $U(1)_\ell$ is spontaneously broken by an SM singlet scalar $\phi$
                with mass $m_\phi$ and lepton number 3.
                The VEV is set to $v_\phi = 2\,\text{TeV}$.
                Four different scenarios for the masses of the DM
                ($m_\text{DM}$) and additional leptons ($m_\text{HL}$)
                are considered.
                """),
            T_star=500,
            g_star=130,
            v_wall=1.0,
            mission_profile=DEFAULT_MISSION_PROFILE,
            has_scenarios=True
        )
        gauged_lepton_madge.save()

        scenario_a = Scenario(
            model=gauged_lepton_madge,
            number=1,
            name="Scenario A",
            description=r"$m_\text{DM} = 0$, $m_\text{HL} = 0$"
        )
        scenario_a.save()

        scenario_b = Scenario(
            model=gauged_lepton_madge,
            number=2,
            name="Scenario B",
            description=r"$m_\text{DM} = 200\,\text{GeV}$, $m_\text{HL} = 210\,\text{GeV}$ "
        )
        scenario_b.save()

        scenario_c = Scenario(
            model=gauged_lepton_madge,
            number=3,
            name="Scenario C",
            description=r"$m_\text{DM} = 500\,\text{GeV}$, $m_\text{HL} = 1\,\text{TeV}$"
        )
        scenario_c.save()

        scenario_d = Scenario(
            model=gauged_lepton_madge,
            number=4,
            name="Scenario D",
            description=r"$h^2\Omega_\text{DM} = 0.12$, $m_\text{HL} = 1.5\,m_\text{DM}$"
        )
        scenario_d.save()

        points: DataFrame = read_csv(
            os.path.join(FILEDIR, "BenchmarksGaugedLeptonNumber.csv"),
            sep=",",
            dtype={
                "vPhi": np.int_,
                "mPhi": np.int_,
                "mZp": np.int_,
                "mDM": np.int_,
                "mHL": np.int_,
                "Tn": np.float64,
                "alpha": np.float64,
                "betaoverH": np.float64,
                "vw": np.float64,  # These are all 1 in the file, though.
                "gstar": np.float64,
                "label": str
            },
            engine="c",
            skipinitialspace=True
        )
        scenarios: dict[str, Scenario] = {
            "A": scenario_a,
            "B": scenario_b,
            "C": scenario_c,
            "D": scenario_d
        }
        for row in points.itertuples():
            letter = row.label[0]
            point = ParameterChoice(
                model=gauged_lepton_madge,
                number=row.Index + 1,  # type: ignore
                long_label=rf"{letter}: $(m_\phi, m_{{Z'}}) = ({row.mPhi:d},{row.mZp:d})\, \mathrm{{GeV}}$",
                T_star=row.Tn,
                alpha=row.alpha,
                beta_over_H=row.betaoverH,
                g_star=row.gstar,
                scenario=scenarios[letter]
            )
            point.save()

        return gauged_lepton_madge

    @staticmethod
    def randall_sundrum() -> Model:
        rs_model = Model(
            name="Randall-Sundrum model benchmark points",
            slug="randall-sundrum",
            description=(
                "Benchmark points for the holographic phase transition in Randall-Sundrum models "
                "(supplied by G. Nardini)."
            ),
            notes="",
            T_star=500,
            g_star=106.75,
            v_wall=0.95,
            mission_profile=DEFAULT_MISSION_PROFILE,
            has_scenarios=False,
            huge_alpha=True
        )
        rs_model.save()

        pb1 = ParameterChoice(
            model=rs_model,
            number=1,
            short_label="B1",
            long_label="$B_1$",
            T_star=1053,
            alpha=1.60,
            beta_over_H=10**2.36
        )
        pb1.save()

        pb2 = ParameterChoice(
            model=rs_model,
            number=2,
            short_label="B2",
            long_label="$B_2$",
            T_star=821.8,
            alpha=4.61,
            beta_over_H=10**1.99
        )
        pb2.save()

        pb3 = ParameterChoice(
            model=rs_model,
            number=3,
            short_label="B3",
            long_label="$B_3$",
            T_star=770.4,
            alpha=7.86,
            beta_over_H=10**1.79
        )
        pb3.save()

        pb4 = ParameterChoice(
            model=rs_model,
            number=4,
            short_label="B4",
            long_label="$B_4$",
            T_star=730.6,
            alpha=17.1,
            beta_over_H=10**1.48
        )
        pb4.save()

        pb5 = ParameterChoice(
            model=rs_model,
            number=5,
            short_label="B5",
            long_label="$B_5$",
            T_star=694.0,
            alpha=90.1,
            beta_over_H=10**1.97
        )
        pb5.save()

        pb6 = ParameterChoice(
            model=rs_model,
            number=6,
            short_label="B6",
            long_label="$B_6$",
            T_star=694.0,
            alpha=90.1,
            beta_over_H=10**1.97
        )
        pb6.save()

        pb7 = ParameterChoice(
            model=rs_model,
            number=7,
            short_label="B7",
            long_label="$B_7$",
            T_star=612.0,
            alpha=1047,
            beta_over_H=10**1.67
        )
        pb7.save()

        pb8 = ParameterChoice(
            model=rs_model,
            number=8,
            short_label="B8",
            long_label="$B_8$",
            T_star=566.4,
            alpha=4e4,
            beta_over_H=10**1.23
        )
        pb8.save()

        pb9 = ParameterChoice(
            model=rs_model,
            number=9,
            short_label="B9",
            long_label="$B_9$",
            T_star=549.3,
            alpha=4.1e6,
            beta_over_H=10**0.64
        )
        pb9.save()

        pb10 = ParameterChoice(
            model=rs_model,
            number=10,
            short_label="B10",
            long_label="$B_{10}$",
            T_star=546.8,
            alpha=3.3e7,
            beta_over_H=10**0.34
        )
        pb10.save()

        pb11 = ParameterChoice(
            model=rs_model,
            number=11,
            short_label="B11",
            long_label="$B_{11}$",
            T_star=545.6,
            alpha=4.5e8,
            beta_over_H=10**-0.32
        )
        pb11.save()

        pc1 = ParameterChoice(
            model=rs_model,
            number=12,
            short_label="C1",
            long_label="$C_1$",
            T_star=578.4,
            alpha=4.3,
            beta_over_H=10**2.03
        )
        pc1.save()

        pc2 = ParameterChoice(
            model=rs_model,
            number=13,
            short_label="C2",
            long_label="$C_2$",
            T_star=416.2,
            alpha=5e3,
            beta_over_H=10**1.45
        )
        pc2.save()

        pd1 = ParameterChoice(
            model=rs_model,
            number=14,
            short_label="D1",
            long_label="$D_1$",
            T_star=133.7,
            alpha=5.0,
            beta_over_H=10**1.05
        )
        pd1.save()

        pe1 = ParameterChoice(
            model=rs_model,
            number=15,
            short_label="E1",
            long_label="$E_1$",
            T_star=567.2,
            alpha=203,
            beta_over_H=10**1.89
        )
        pe1.save()

        return rs_model

    @staticmethod
    def singlet_jonathan() -> Model:
        singlet_jonathan = Model(
            name="Singlet scalar benchmark points",
            slug="singlet_jonathan",
            description=(
                "Benchmark points for the SM extended with a general real singlet scalar field, $S$ "
                "(supplied by J. Kozaczuk)."
            ),
            notes=cleandoc(r"""
                $$
                \Delta V = b_1 S
                + \frac{1}{2} b_2 S^2
                + \frac{1}{2} a_1 S \left| H \right|^2
                + \frac{1}{2} a_2 S^2 \left| H \right|^2
                + \frac{1}{3} b_3 S^3
                + \frac{1}{4} b_4 S^4.
                $$

                In the mass basis, the mass-ordered eigenstates are $m_{1,2}$.
                The mixing angle between $S$ and $H$ is denoted as $\theta$.
                Masses considered are $m_2 = 170,\, 240\, \mathrm{GeV}$.
                We show results for points with $m_2= 170,\, 240\, \mathrm{GeV}$ and $\sin \theta = 0.1$,
                which are likely to be probed by direct searches at the high-luminosity LHC with
                $3\, \mathrm{ab}^{-1}$, and $\sin\theta = 0.01$, which will likely remain undetected at colliders.
                The various parameters in the potential are scanned over as described in the text.
                See also JHEP 1708 (2017) 096 [https://arxiv.org/abs/arXiv:1704.05844] for more details.
                """),
            T_star=50,
            g_star=107.75,
            v_wall=1.0,
            mission_profile=DEFAULT_MISSION_PROFILE,
            has_scenarios=True
        )
        singlet_jonathan.save()

        scenario1 = Scenario(
            model=singlet_jonathan,
            number=1,
            name="Not probed by HL-LHC",
            description="Set of points that are not probed by HL-LHC"
        )
        scenario1.save()

        scenario2 = Scenario(
            model=singlet_jonathan,
            number=2,
            name="Will be probed by HL-LHC",
            description="Set of points that will be probed by HL-LHC"
        )
        scenario2.save()

        # File contents: alpha, beta_over_H, probe
        # points: DataFrame = read_csv(
        #     os.path.join(FILEDIR, "GW_singlet_combined.dat"),
        #     sep=",",
        #     skipinitialspace=True
        # )
        points: DataFrame = read_csv(
            os.path.join(FILEDIR, "GW_singlet_combined_all_params.dat"),
            sep=",",
            dtype=defaultdict(lambda: np.float64, {"LHCflag": np.bool_}),
            engine="c",
            skipinitialspace=True
        )
        for row in points.itertuples():
            point = ParameterChoice(
                model=singlet_jonathan,
                number=row.Index + 1,  # type: ignore
                long_label=(
                    rf"$m_2 = {row.m2:.0f}\, \mathrm{{GeV}}$, $\sin \theta = {row.sinTheta:g}$, "
                    rf"$a_2 = {row.a2:g}$, $b_3 = {row.b3:g}$, $b_4  = {row.b4:g}$"
                ),
                alpha=row.alpha,
                T_star=row.Tstar,
                beta_over_H=row.betaoverH,
                scenario=scenario2 if row.LHCflag else scenario1
            )
            point.save()

        return singlet_jonathan

    @staticmethod
    def singlet_jonathan_z2() -> Model:
        singlet_jonathan_z2 = Model(
            name="$Z_2$-symmetric singlet scalar benchmark points",
            slug="singlet_jonathan_z2",
            description=(
                "Benchmark points for the SM extended with a scalar singlet "
                "with $Z_2$ symmetry (supplied by J. Kozaczuk)."
            ),
            notes=cleandoc(r"""
                The new physics potential reads
                $$\Delta V = \frac{1}{2}a_2 |H|^2 S^2 + \frac{1}{2} b_2 S^2 + \frac{1}{4} b_4 S^4.$$

                The parameter $m$ below stands for the physical mass of the singlet.
                For each pair $(m, a_2)$, the remaining free parameter,
                namely the singlet self coupling $b_4$,
                is taken to be the one that maximizes the strength of the phase transition,
                computed using a modified version of CosmoTransitions
                (see https://arxiv.org/abs/1109.4189).
                """),
            T_star=50,
            g_star=106.75,
            v_wall=1.0,
            mission_profile=DEFAULT_MISSION_PROFILE,
            has_scenarios=False
        )
        singlet_jonathan_z2.save()

        points: DataFrame = read_csv(
            os.path.join(FILEDIR, "GW_singlet_Z2.dat"),
            sep=",",
            dtype=np.float64,
            engine="c",
            skipinitialspace=True,
        )
        for row in points.itertuples():
            point = ParameterChoice(
                model=singlet_jonathan_z2,
                number=row.Index + 1,  # type: ignore
                long_label=rf"$m = {row.m:.0f}\, \mathrm{{GeV}}, \, a_2 = {row.a2:.1f}$",
                T_star=row.Tstar,
                alpha=row.alpha,
                beta_over_H=row.betaoverH
            )
            point.save()

        return singlet_jonathan_z2

    @staticmethod
    def singlet_miki() -> Model:
        singlet_miki = Model(
            name="$Z_2$-symmetric singlet scalar benchmark points",
            slug="singlet_miki",
            description=(
                "Benchmark points for the SM extended with a scalar singlet with "
                "$Z_2$ symmetry (supplied by M. Chala)."
            ),
            notes=cleandoc(r"""
                The new physics potential reads
                $$\Delta V = \frac{1}{2}a_2 |H|^2 S^2 + \frac{1}{2} b_2 S^2 + \frac{1}{4}
                b_4 S^4.$$

                The parameter $m$ below stands for the physical mass of the singlet.
                For each pair $(m, a_2)$, the remaining free parameter,
                namely the singlet self coupling $b_4$,
                is taken to be the one that maximizes the strength of the phase transition,
                computed using a modified version of CosmoTransitions
                (see https://arxiv.org/abs/1109.4189).
                """),
            T_star=50,
            g_star=106.75,
            v_wall=1.0,
            mission_profile=DEFAULT_MISSION_PROFILE,
            has_scenarios=False
        )
        singlet_miki.save()

        points: DataFrame = read_csv(
            os.path.join(FILEDIR, "miki_singlet_portal.txt"),
            sep=" ",
            dtype=np.float64,
            engine="c",
        )
        for row in points.itertuples():
            point = ParameterChoice(
                model=singlet_miki,
                number=row.Index + 1,  # type: ignore
                long_label=rf"$m = {row.m:.0f}\, \mathrm{{GeV}}, \, a_2 = {row.a2:g}$",
                T_star=row.Tstar,
                alpha=row.alpha,
                beta_over_H=row.betaoverH
            )
            point.save()

        return singlet_miki

    @staticmethod
    def singlet_portal() -> Model:
        singlet_portal = Model(
            name="Singlet (Higgs Portal) benchmark points",
            slug="singlet_portal",
            description=(
                "Real singlet extension of the Standard Model with $Z_2$ symmetry, "
                r"with $m_S = 250\, \mathrm{GeV}$."
            ),
            notes=cleandoc(r"""
                Benchmark points from https://arxiv.org/abs/1512.06239.
                Data from Table 3, see potential, Eq. (30), for details of potential parameters $(a_2,b_4)$.
                $T_*$ is taken to be $50\, \mathrm{GeV}$ for the plot.
                """),
            T_star=50,
            g_star=106.75,
            v_wall=0.95,
            model_Senscurve=0,
            has_scenarios=False
        )
        singlet_portal.save()

        pa = ParameterChoice(
            model=singlet_portal,
            number=1,
            short_label=r"A",
            long_label=r"$(a_2,b_4) = (2.8,2.1)$",
            T_star=70.6,
            alpha=0.09,
            beta_over_H=47.35
        )
        pa.save()

        pb = ParameterChoice(
            model=singlet_portal,
            number=2,
            short_label=r"B",
            long_label=r"$(a_2,b_4) = (2.9,2.6)$",
            T_star=65.2,
            alpha=0.12,
            beta_over_H=29.96
        )
        pb.save()

        pc = ParameterChoice(
            model=singlet_portal,
            number=3,
            short_label=r"C",
            long_label=r"$(a_2,b_4) = (3.0,3.3)$",
            T_star=49.6,
            alpha=0.17,
            beta_over_H=12.54
        )
        pc.save()

        pd = ParameterChoice(
            model=singlet_portal,
            number=4,
            short_label=r"D",
            long_label=r"$(a_2,b_4) = (3.1,4.0)$",
            T_star=56.4,
            alpha=0.20,
            beta_over_H=6.42
        )
        pd.save()

        return singlet_portal

    @staticmethod
    def singlet_scalars_moritz() -> Model:
        singlet_scalars = Model(
            name="Scalar dark sector benchmark points",
            slug="singlet_scalars_moritz",
            description=(
                "Benchmark points for a model with two gauge singlet scalars in a hidden sector "
                "(supplied by M. Breitbach)."
            ),
            notes=cleandoc("""
                The underlying random parameter scan contains 1000 points.
                Note that not all of these points fall into the plotted regions.
                The Lagrangian as well as the parameter regions used for the scatter plots are given in Section III of
                https://arxiv.org/abs/1811.11175
                """),
            T_star=100,
            g_star=106.75,
            v_wall=0.95,
            mission_profile=DEFAULT_MISSION_PROFILE,
            has_scenarios=False
        )
        singlet_scalars.save()

        points: DataFrame = read_csv(
            os.path.join(FILEDIR, "datapoints_TwoRealScalarSinglets.csv"),
            sep=",",
            dtype=np.float64,
            engine="c",
        )
        points.T_nuc *= 200  # scale factor
        for row in points.itertuples():
            point = ParameterChoice(
                model=singlet_scalars,
                number=row.Index + 1,  # type: ignore
                long_label=f"Point {row.Index + 1:d}",  # type: ignore
                T_star=row.T_nuc,
                alpha=row.alpha,
                beta_over_H=row.beta_per_H,
                g_star=row.rel_dof
            )
            point.save()

        return singlet_scalars

    @staticmethod
    def susy():
        susy = Model(
            name="Some SUSY embeddings",
            slug="susy",
            description=(
                "Benchmark points for some SUSY embeddings with chiral "
                "supersinglets or supertriplets (supplied by G. Nardini)."
            ),
            notes=cleandoc("""
                The benchmark points SUSY$_1$ are taken from
                https://arxiv.org/abs/1512.06357, SUSY$_2$ from
                https://arxiv.org/abs/1704.02488, SUSY$_3$ from
                https://arxiv.org/abs/1712.00087, and SUSY$_4$ from
                https://arxiv.org/abs/1602.01351 .
                Details on the models can be found in the corresponding references.
                """),
            T_star=100,
            g_star=108.75,
            v_wall=0.95,
            mission_profile=DEFAULT_MISSION_PROFILE,
            has_scenarios=True
        )
        susy.save()

        scenario1 = Scenario(
            model=susy,
            number=1,
            name="SUSY$_1$",
            T_star=100,
            description="(this scenario has 2 benchmark points)"
        )
        scenario1.save()

        p1_a = ParameterChoice(
            model=susy,
            number=1,
            short_label="1A",
            long_label="SUSY$_1$ point A",
            T_star=112,
            alpha=0.037,
            beta_over_H=277,
            scenario=scenario1
        )
        p1_a.save()

        p1_b = ParameterChoice(
            model=susy,
            number=2,
            short_label="1B",
            long_label="SUSY$_1$ point B",
            T_star=95,
            alpha=0.066,
            beta_over_H=106,
            scenario=scenario1
        )
        p1_b.save()

        p1_c = ParameterChoice(
            model=susy,
            number=3,
            short_label="1C",
            long_label="SUSY$_1$ point C",
            T_star=82,
            alpha=0.105,
            beta_over_H=33,
            scenario=scenario1
        )
        p1_c.save()

        p1_d = ParameterChoice(
            model=susy,
            number=4,
            short_label="1D",
            long_label="SUSY$_1$ point D",
            T_star=76.4,
            alpha=0.143,
            beta_over_H=6.0,
            scenario=scenario1
        )
        p1_d.save()

        scenario2 = Scenario(
            model=susy,
            number=2,
            name="SUSY$_2$",
            T_star=140,
            description="(this scenario has 2 benchmark points)"
        )
        scenario2.save()

        p2_a = ParameterChoice(
            model=susy,
            number=5,
            short_label="2A",
            long_label="SUSY$_2$ point A",
            T_star=135,
            alpha=0.050,
            beta_over_H=830,
            v_wall=0.73,
            scenario=scenario2
        )
        p2_a.save()

        p2_b = ParameterChoice(
            model=susy,
            number=6,
            short_label="2B",
            long_label="SUSY$_2$ point B",
            T_star=146,
            alpha=0.040,
            beta_over_H=2914,
            v_wall=0.72,
            scenario=scenario2
        )
        p2_b.save()

        scenario3 = Scenario(
            model=susy,
            number=3,
            name="SUSY$_3$",
            T_star=75,
            description="(this scenario has 4 benchmark points)"
        )
        scenario3.save()

        p3_a = ParameterChoice(
            model=susy,
            number=7,
            short_label="3A",
            long_label="SUSY$_3$ point A",
            T_star=74,
            alpha=0.062,
            beta_over_H=214,
            v_wall=0.1,
            scenario=scenario3
        )
        p3_a.save()

        p3_b = ParameterChoice(
            model=susy,
            number=8,
            short_label="3B",
            long_label="SUSY$_3$ point B",
            T_star=74,
            alpha=0.062,
            beta_over_H=214,
            v_wall=0.5,
            scenario=scenario3
        )
        p3_b.save()

        p3_c = ParameterChoice(
            model=susy,
            number=9,
            short_label="3C",
            long_label="SUSY$_3$ point C",
            T_star=79,
            alpha=0.045,
            beta_over_H=200,
            v_wall=0.1,
            scenario=scenario3
        )
        p3_c.save()

        p3_d = ParameterChoice(
            model=susy,
            number=10,
            short_label="3D",
            long_label="SUSY$_3$ point D",
            T_star=79,
            alpha=0.045,
            beta_over_H=200,
            v_wall=0.5,
            scenario=scenario3
        )
        p3_d.save()

        scenario4 = Scenario(
            model=susy,
            number=4,
            name="SUSY$_4$",
            T_star=100,
            description="(this scenario has 1 benchmark points)"
        )
        scenario4.save()

        p4_a = ParameterChoice(
            model=susy,
            number=11,
            short_label="4A",
            long_label="SUSY$_4$ point A",
            T_star=48,
            alpha=0.22,
            beta_over_H=57,
            v_wall=0.95,
            scenario=scenario4
        )
        p4_a.save()

    @staticmethod
    def twohdm_josemi() -> None:
        twohdm_josemi = Model(
            name="2HDM benchmark points",
            slug="twohdm_josemi",
            description=(
                "Benchmark points for the two-Higgs-doublet model with a softly-broken $Z_2$ symmetry "
                "(supplied by G. Dorsch and J.M. No)."
            ),
            notes=cleandoc(r"""
                Benchmark points for the two-Higgs-doublet model (2HDM)
                with a softly-broken $Z_{2}$ symmetry, with scalar potential
                \begin{eqnarray}
                V(H_1,H_2) & =
                & \mu^2_1 \left|H_1\right|^2
                + \mu^2_2\left|H_2\right|^2
                - \mu^2 \left[H_1^{\dagger}H_2+\mathrm{h.c.}\right]
                + \frac{\lambda_1}{2}\left|H_1\right|^4
                + \frac{\lambda_2}{2}\left|H_2\right|^4 \nonumber \\
                &  & + \lambda_3 \left|H_1\right|^2\left|H_2\right|^2
                + \lambda_4 \left|H_1^{\dagger}H_2\right|^2
                + \frac{\lambda_5}{2}\left[\left(H_1^{\dagger}H_2\right)^2+\mathrm{h.c.}\right] \, , \nonumber
                \end{eqnarray}
                In the mass basis, there are three new physical states in addition to the 125 GeV Higgs $h$:
                a charged scalar $H^{\pm}$ and two neutral states $H_0$, $A_0$.
                Apart from their masses, the 2HDM features as free parameters two angles
                ($\beta$ and $\alpha$) and $\mu^2$.
                In the following results we consider $m_{H^{\pm}} = m_{A_0}$,
                $\mathrm{cos} (\beta - \alpha) = 0$ (the 2HDM alignment limit) an fix for convenience
                $\mu^2 (\mathrm{tan} \beta + \mathrm{tan}^{-1} \beta) = m_{H_0}^2$.
                Results are shown for benchmarks in $m_{H_0} \in [180\,\mathrm{GeV},\,\,450\,\mathrm{GeV}]$ and
                $m_{A_0} \in [m_{H_0}+ 150\,\mathrm{GeV} ,\,\,m_{H_0} + 350\,\mathrm{GeV}]$.
                """),
            T_star=50,
            g_star=106.75,
            v_wall=0.7,
            mission_profile=DEFAULT_MISSION_PROFILE,
            has_scenarios=True
        )
        twohdm_josemi.save()

        scenario1 = Scenario(
            model=twohdm_josemi,
            number=1,
            name="Set 1",
            description=cleandoc(r"""
                2HDM points which are currently allowed both for Type I and Type II 2HDM.
                For Type II, these will be probed by the LHC in the future,
                while for Type I the LHC will not be able to exclude these benchmarks,
                depending on the value of $\tan\beta$ (which does not influence the strength of the PT).
                """
            )
        )
        scenario1.save()

        points1: DataFrame = read_csv(
            os.path.join(FILEDIR, "josemi_2hdm.txt"),
            sep=",",
            dtype=np.float64,
            engine="c",
            skipinitialspace=True,
            comment="#"
        )
        first_set_point_count = len(points1.index)
        for row in points1.itertuples():
            point = ParameterChoice(
                model=twohdm_josemi,
                number=row.Index + 1,  # type: ignore
                long_label=
                    rf"$(m_H,m_A) = ({row.mH:.0f},{row.mA:.0f}) \, \mathrm{{GeV}}$, $\tan \beta = {row.tanb:.0f}$",
                T_star=row.Tn,
                alpha=row.alpha_n,
                beta_over_H=row.beta_H_n,
                scenario=scenario1
            )
            point.save()

        scenario2 = Scenario(
            model=twohdm_josemi,
            number=2,
            name="Set 2",
            description=(
                "2HDM points which are currently allowed for Type I 2HDM, "
                "but excluded for Type II 2HDM, by LHC searches."
            )
        )
        scenario2.save()

        # The comment in the file says:
        # SET 2 (YELLOW/GOLD points): 2HDM points which are currently allowed
        # for Type I 2HDM, but excluded for Type II 2HDM, by LHC searches.
        points2: DataFrame = read_csv(
            os.path.join(FILEDIR, "josemi_2hdm_set2.txt"),
            sep=",",
            dtype=np.float64,
            engine="c",
            skipinitialspace=True,
            comment="#"
        )
        for row in points2.itertuples():
            point = ParameterChoice(
                model=twohdm_josemi,
                number=first_set_point_count + row.Index + 1,  # type: ignore
                long_label=
                    rf"$(m_H,m_A) = ({row.mH:.0f},{row.mA:.0f}) \, \mathrm{{GeV}}$, $\tan \beta = {row.tanb:.0f}$",
                T_star=row.Tn,
                alpha=row.alpha_n,
                beta_over_H=row.beta_H_n,
                scenario=scenario2
            )
            point.save()

    def handle(self, *args, **options):
        """Populate the database with benchmark models, scenarios and points"""
        print("Populating DB...")
        # This order determines the indices of the models.
        # The visible order of the models is set in Model.Meta.
        self.twohdm_josemi()
        self.singlet_jonathan_z2()
        self.singlet_scalars_moritz()
        self.dark_photon_moritz()
        self.gauged_lepton_madge()
        self.composite()
        self.susy()
        self.singlet_jonathan()
        # self.singlet_portal()
        # self.singlet_miki()
        print("DB populated.")
        print("NOTE: If you want to clear the tables, run \"python3 manage.py flush\".")
