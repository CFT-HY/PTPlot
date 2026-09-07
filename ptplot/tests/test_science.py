"""Tests for the science module."""

from django.test import TestCase

from ptplot.science.plot.snr_alpha_beta import snr_figure_alpha_beta
from ptplot.science.plot.snr_ubarf_rstar import snr_figure_ubarf_rstar
import ptplot.science.sensitivity.sciencerequirements as req
from ptplot.science.snr_grid_alpha_beta import SNRGridAlphaBeta
from ptplot.science.snr_grid_ubarf_rstar import SNRGridUbarfRStar
from ptplot.science.spectrum.create import power_spectrum
from ptplot.science.spectrum.engine import Engine

V_WALL: float = 0.3
ALPHA: float = 0.1
BETA_OVER_H: float = 10000
T_STAR: float = 100
G_STAR: float = 100


class ScienceTest(TestCase):
    """Tests for the science module."""

    @staticmethod
    def test_power_spectrum():
        power_spectrum(v_wall=V_WALL, alpha=ALPHA, beta_over_H=BETA_OVER_H)

    @staticmethod
    def test_power_spectrum_dbpl():
        power_spectrum(v_wall=V_WALL, alpha=ALPHA, beta_over_H=BETA_OVER_H, engine=Engine.DBPL)

    @staticmethod
    def test_power_spectrum_ssm():
        power_spectrum(v_wall=V_WALL, alpha=ALPHA, beta_over_H=BETA_OVER_H, engine=Engine.SSM)

    @staticmethod
    def test_power_spectrum_ssm_const_cs():
        power_spectrum(v_wall=V_WALL, alpha=ALPHA, beta_over_H=BETA_OVER_H, engine=Engine.SSM, css2=1 / 4, csb2=1 / 4)

    @staticmethod
    def test_requirements():
        req.main(print_points=False)

    @staticmethod
    def test_snr_alpha_beta():
        snr_figure_alpha_beta(
            grid=SNRGridAlphaBeta(
                T_star=T_STAR, g_star=G_STAR, v_wall=V_WALL,
                alpha_points=ALPHA, beta_over_H_points=BETA_OVER_H, v_wall_points=V_WALL
            )
        )

    @staticmethod
    def test_snr_ubarf_rstar():
        snr_figure_ubarf_rstar(
            grid=SNRGridUbarfRStar(
                T_star=T_STAR, g_star=G_STAR, v_wall=V_WALL,
                alpha_points=ALPHA, beta_over_H_points=BETA_OVER_H, v_wall_points=V_WALL
            )
        )
