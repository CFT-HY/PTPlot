from django.test import TestCase

from ptplot.science.calculate_powerspectrum import PowerSpectrum
import ptplot.science.sensitivity.sciencerequirements as req
import ptplot.science.espinosa as esp
import ptplot.science.plot_powerspectrum as plot_ps
# import ptplot.science.snr as snr
# import ptplot.science.SNR_precompute as snr_pre
import ptplot.science.SNRalphabeta_onthefly as snr_ab
import ptplot.science.SNRubarfrstar_onthefly as snr_ubarf


class ScienceTest(TestCase):
    def test_requirements(self):
        req.main()

    def test_power_spectrum(self):
        PowerSpectrum(vw=0.3, alpha=0.1, BetaoverH=10000)

    def test_ubarf(self):
        esp.ubarf(vw=0.7, alpha=0.1)

    def test_kappav(self):
        esp.kappav(vw=0.7, alpha=0.1)

    def test_ubarf_to_alpha(self, vw: float = 0.7):
        ubarf = esp.ubarf(vw=0.7, alpha=0.1)
        esp.ubarf_to_alpha(ubarf, this_ubarf=ubarf)

    def test_get_ps_data(self):
        plot_ps.get_PS_data()

    def test_get_ps_image(self):
        plot_ps.get_PS_image()

    # def test_load_file(self):
    #     snr.LoadFile()

    # def test_stock_bkg_compute_snr(self):
    #     snr.StockBkg_ComputeSNR()

    # def test_get_snr_curve(self):
    #     snr_pre.get_SNRcurve()

    def test_get_snr_alpha_beta_image(self):
        snr_ab.get_SNR_alphabeta_image(vw=0.3)

    def test_snr_ubarf(self):
        snr_ubarf.get_SNR_image()
