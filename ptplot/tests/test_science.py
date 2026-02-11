"""Tests for the science module"""

from django.test import TestCase

import ptplot.science.sensitivity.sciencerequirements as req
import ptplot.science.espinosa as esp
from ptplot.science.plot.power_spectrum import ps_figure
from ptplot.science.engine import Engine
from ptplot.science.spectrum.create import PowerSpectrumBPL, power_spectrum
from ptplot.science.plot.snr_alpha_beta import snr_figure_alpha_beta
from ptplot.science.plot.snr_ubarf_rstar import snr_figure_ubarf_rstar

VW: float = 0.3
ALPHA: float = 0.1
BETA_OVER_H: float = 10000


class ScienceTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.spectrum = PowerSpectrumBPL(vw=VW, alpha=ALPHA, beta_over_H=BETA_OVER_H)

    def test_csv(self):
        self.spectrum.csv()

    def test_kappa_v(self):
        esp.kappa_v(v_wall=0.7, alpha_n=0.1)

    def test_power_spectrum(self):
        power_spectrum(vw=VW, alpha=ALPHA, beta_over_H=BETA_OVER_H)

    def test_power_spectrum_dbpl(self):
        power_spectrum(vw=VW, alpha=ALPHA, beta_over_H=BETA_OVER_H, engine=Engine.DBPL)

    def test_power_spectrum_ssm(self):
        power_spectrum(vw=VW, alpha=ALPHA, beta_over_H=BETA_OVER_H, engine=Engine.SSM)

    def test_power_spectrum_ssm_const_cs(self):
        power_spectrum(vw=VW, alpha=ALPHA, beta_over_H=BETA_OVER_H, engine=Engine.SSM, css2=1/4, csb2=1/4)

    def test_ps_image(self):
        ps_figure(self.spectrum, sw_only=False)

    def test_requirements(self):
        req.main(print_points=False)

    def test_snr_alpha_beta_image(self):
        snr_figure_alpha_beta(v_wall=0.3)

    # def test_snr_curve(self):
    #     snr_pre.get_SNRcurve()

    def test_snr_ubarf(self):
        snr_figure_ubarf_rstar()

    # def test_stock_bkg_compute_snr(self):
    #     snr.StockBkg_ComputeSNR()

    def test_ubarf(self):
        esp.ubarf(v_wall=0.7, alpha_n=0.1)

    def test_ubarf_to_alpha(self, vw: float = 0.7):
        ubarf = esp.ubarf(v_wall=0.7, alpha_n=0.1)
        esp.alpha_n_from_ubarf(ubarf, ubarf=ubarf)
