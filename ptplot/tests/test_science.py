from django.test import TestCase

import ptplot.science.sensitivity.sciencerequirements as req
import ptplot.science.espinosa as esp
import ptplot.science.plot_powerspectrum as plot_ps
from ptplot.science.powerspectrum import PowerSpectrum
# from ptplot.science.powerspectrum_dbpl import PowerSpectrumDBPL
# from ptplot.science.powerspectrum_ssm import PowerSpectrumSSM
# import ptplot.science.snr as snr
# import ptplot.science.SNR_precompute as snr_pre
import ptplot.science.snr_alphabeta_onthefly as snr_ab
import ptplot.science.snr_ubarfrstar_onthefly as snr_ubarf

VW: float = 0.3
ALPHA: float = 0.1
BETA_OVER_H: float = 10000


class ScienceTest(TestCase):
    def test_kappav(self):
        esp.kappav(vw=0.7, alpha=0.1)

    # def test_load_file(self):
    #     snr.LoadFile()

    def test_power_spectrum(self):
        PowerSpectrum(vw=VW, alpha=ALPHA, beta_over_H=BETA_OVER_H)

    # def test_power_spectrum_dbpl(self):
    #     PowerSpectrumDBPL(vw=VW, alpha=ALPHA, beta_over_H=BETA_OVER_H)
    #
    # def test_power_spectrum_ssm(self):
    #     PowerSpectrumSSM(vw=VW, alpha=ALPHA, beta_over_H=BETA_OVER_H)

    def test_ps_data(self):
        plot_ps.get_ps_data()

    def test_ps_image(self):
        plot_ps.get_ps_image()

    def test_requirements(self):
        req.main(print_points=False)

    def test_snr_alpha_beta_image(self):
        snr_ab.get_snr_alphabeta_image(vw=0.3)

    # def test_snr_curve(self):
    #     snr_pre.get_SNRcurve()

    def test_snr_ubarf(self):
        snr_ubarf.get_snr_image()

    # def test_stock_bkg_compute_snr(self):
    #     snr.StockBkg_ComputeSNR()

    def test_ubarf(self):
        esp.ubarf(vw=0.7, alpha=0.1)

    def test_ubarf_to_alpha(self, vw: float = 0.7):
        ubarf = esp.ubarf(vw=0.7, alpha=0.1)
        esp.ubarf_to_alpha(ubarf, this_ubarf=ubarf)
