r"""GW power spectra of hydrodynamic lattice simulations, converted to the GW power spectrum today.

The simulations are those of :py:mod:`pttools.lattice`, e.g. the runs of :correia_2025:`\ `,
see :py:func:`pttools.lattice.chrw25.load_chrw25_runs`.
The simulated GW power spectra are converted to the GW power spectrum today in two ways:

- From the GW power spectrum $\mathcal{P}_\text{gw}$ that has accumulated by the time step,
  as in PTtools, see :py:class:`pttools.lattice.spectrum.LatticeSpectrum`.
  The simulation is considered as a source that has lasted from its start to the time step,
  and its GW power is reduced by the expansion of the universe during this time
  in the same way as that of the Sound Shell Model.
  The simulations end before the GW power has stopped growing.
  Therefore, the spectrum can be scaled to the asymptotic GW power,
  which is extrapolated with :correia_2025:`\ ` eq. 47,
  see :py:attr:`PowerSpectrumLattice.omgw0_h2_asymptote`.
- From the GW power growth rate $\dot{\mathcal{P}}_\text{gw}$ at the time step,
  with the source lifetime and the expansion of the universe of the Sound Shell Model,
  see :py:attr:`PowerSpectrumLattice.omgw0_h2_rate`.

The simulations are scale-free, as $H_n$ only enters through the Friedmann equation.
Therefore, the spectra can be evaluated at any $r_*$.
"""

from enum import StrEnum
import functools
import typing as tp

import numpy as np
from pttools.bubble import Bubble
from pttools.lattice import LatticeRun
from pttools.lattice import LatticeSpectrum as PTtoolsLatticeSpectrum
from pttools.omgw0 import Spectrum
from pttools.ssm.suppression.fit import lattice_artifact_start

from ptplot.science import const
from ptplot.science.noise import Noise
from ptplot.science.spectrum.base import PowerSpectrum
from ptplot.science.spectrum.ssm import BAG
from ptplot.science.type_hints import FloatArr1D

__all__ = ["CHRW25_NAME", "LatticeConversion", "PowerSpectrumLattice"]

#: Name of the simulations of :correia_2025:`\ ` in the labels of the figures
CHRW25_NAME: str = "CHRW25sim"


class LatticeConversion(StrEnum):
    """Conversions of the simulated GW power to the GW power spectrum today, see :py:class:`PowerSpectrumLattice`."""

    #: From the accumulated GW power, see :py:attr:`PowerSpectrumLattice.omgw0_h2`
    ACCUMULATED = "accumulated"
    #: From the accumulated GW power scaled to the asymptote, see :py:attr:`PowerSpectrumLattice.omgw0_h2_asymptote`
    ASYMPTOTE = "asymptote"
    #: From the GW power growth rate, see :py:attr:`PowerSpectrumLattice.omgw0_h2_rate`
    RATE = "rate"


class PowerSpectrumLattice(PowerSpectrum):
    r"""GW power spectrum of a lattice simulation at a time step, converted to the GW power spectrum today.

    The simulated spectra are given at the frequencies :py:attr:`f`, which correspond to the wavenumbers
    of the simulation, and they are valid only below the lattice artifact at high $k$,
    see :py:attr:`valid` and :py:attr:`valid_rate`.
    :py:meth:`power_spectrum` interpolates the spectrum of the chosen :py:attr:`conversion` to other frequencies.

    The parameters of the base class are those of the simulation:
    $v_\text{wall}$ and $\alpha_n$ of the run, and $r_*$, $T_*$ and $g_*$ of the spectrum.
    The lattice simulations are not an engine, and therefore this class has no :py:attr:`ENGINE`.
    """

    COLOR = "black"
    NAME = "Lattice simulation"
    SHORT_NAME = "lattice"

    def __init__(
            self,
            run: LatticeRun,
            step: int | None = None,
            step_prev: int | None = None,
            r_star: float | None = None,
            T_star: float = const.DEFAULT_T_STAR,
            g_star: float = const.DEFAULT_G_STAR,
            step_end: int | None = None,
            name: str = SHORT_NAME,
            conversion: LatticeConversion = LatticeConversion.ASYMPTOTE,
            adiabatic_index: float | None = None,
            asymptote_duration: bool = True):
        r"""Create the spectrum of a run at a time step.

        :param run: the simulation run
        :param step: the time step, defaults to the last time step of the data,
            see :py:meth:`pttools.lattice.run.LatticeRun.last_step`
        :param step_prev: the earlier time step for computing the GW power growth rate,
            which is required for :py:attr:`omgw0_h2_rate`
        :param r_star: $r_*$, Hubble-scaled mean bubble spacing, defaults to that of the simulation,
            see :py:class:`pttools.lattice.spectrum.LatticeSpectrum`
        :param T_star: $T_*$, temperature at the time of GW production in GeV
        :param g_star: $g_*$, degrees of freedom
        :param step_end: last time step of the extrapolation of the GW power to late times,
            see :py:meth:`pttools.lattice.run.LatticeRun.omega_gw_asymptote`.
            Defaults to the last time step of the data, as the extrapolation is sensitive to its last points.
        :param name: name of the simulation in the labels of the figures
        :param conversion: which conversion :py:meth:`power_spectrum` gives
        :param adiabatic_index: $\Gamma$, mean adiabatic index,
            defaults to that of the bag model fluid shell :py:attr:`bubble`, as used by the Sound Shell Model
        :param asymptote_duration: whether to take into account the expansion of the universe in the asymptotic
            spectrum with the duration in which the GW power would reach the asymptote,
            instead of the duration up to the time step,
            see :py:meth:`pttools.lattice.spectrum.LatticeSpectrum.pow_gw_asymptote_scale`
        """
        self.run: LatticeRun = run
        self.step: int = run.last_step() if step is None else step
        self.step_end: int = run.last_step() if step_end is None else step_end
        self.name: str = name
        self.conversion: LatticeConversion = LatticeConversion(conversion)
        self.asymptote_duration: bool = asymptote_duration
        #: The spectrum of PTtools, which is in the units of the simulation
        self.spectrum: PTtoolsLatticeSpectrum = run.spectrum(
            self.step, step_prev, r_star=r_star, T_star=T_star, g_star=g_star
        )
        super().__init__(
            v_wall=run.v_wall, alpha=run.alpha_n, r_star=self.spectrum.r_star, T_star=T_star, g_star=g_star,
            adiabatic_index=self.bubble.mean_adiabatic_index if adiabatic_index is None else adiabatic_index
        )

    @functools.cached_property
    def asymptote_ratio(self) -> float:
        r"""$\mathcal{P}_\text{gw}^\infty / \mathcal{P}_\text{gw}(t)$, ratio of the asymptotic and current GW power.

        See :py:meth:`pttools.lattice.spectrum.LatticeSpectrum.pow_gw_asymptote_ratio`.
        Without :py:attr:`asymptote_duration`, this is the ratio of the asymptotic and current GW energy density
        $\Omega_\text{gw}^\infty / \Omega_\text{gw}(t)$ of the simulation.
        """
        return self.spectrum.pow_gw_asymptote_ratio(asymptote_duration=self.asymptote_duration, step_end=self.step_end)

    @functools.cached_property
    def bubble(self) -> Bubble:
        r"""Bag model fluid shell with the $v_\text{wall}$ and $\alpha_n$ of the simulation."""
        return Bubble(model=BAG, v_wall=self.run.v_wall, alpha_n=self.run.alpha_n)

    @functools.cached_property
    def f(self) -> FloatArr1D:
        r"""$f$, frequencies today in Hz corresponding to the wavenumbers of the simulation."""
        return self.spectrum.f()

    @functools.cached_property
    def omgw0_h2(self) -> FloatArr1D:
        r"""$\Omega_{\text{gw},0} h^2(f)$, GW power spectrum today from the accumulated GW power at the time step.

        $$\Omega_{\text{gw},0} h^2(f) = F_{\text{gw},0} h^2 \, \mathcal{P}_\text{gw}(z, t),$$
        see :py:meth:`pttools.omgw0.base.Omgw0Base.omgw0_h2`,
        where $\mathcal{P}_\text{gw}$ includes the reduction by the expansion of the universe,
        see :py:attr:`pttools.lattice.spectrum.LatticeSpectrum.pow_gw`.
        """
        return self.spectrum.omgw0_h2(om_gamma0_h2=const.OMEGA_PHOTON_H2)

    @functools.cached_property
    def omgw0_h2_asymptote(self) -> FloatArr1D:
        r"""$\Omega_{\text{gw},0} h^2(f)$, GW power spectrum today scaled to the asymptotic GW power.

        $$\Omega_{\text{gw},0}^\infty h^2(f) = F_{\text{gw},0} h^2 \, \mathcal{P}_\text{gw}^\infty(z)
        = \frac{\mathcal{P}_\text{gw}^\infty}{\mathcal{P}_\text{gw}(t)} \Omega_{\text{gw},0} h^2(f),$$
        see :py:attr:`asymptote_ratio` and :py:meth:`pttools.lattice.spectrum.LatticeSpectrum.pow_gw_asymptote`.
        This assumes that the shape of the spectrum no longer changes after the time step.
        """
        spectrum = self.spectrum
        return spectrum.F_gw0_h2(om_gamma0_h2=const.OMEGA_PHOTON_H2) * spectrum.pow_gw_asymptote(
            asymptote_duration=self.asymptote_duration, step_end=self.step_end
        )

    @functools.cached_property
    def omgw0_h2_rate(self) -> FloatArr1D:
        r"""$\Omega_{\text{gw},0} h^2(f)$, GW power spectrum today from the simulated GW power growth rate.

        The simulated growth rate is scaled with the same factors as the Sound Shell Model of PTtools,
        :py:func:`pttools.ssm.spec_den_gw.spec_den_gw_scaling`,
        $$\Omega_{\text{gw},0} h^2(f) = F_{\text{gw},0} h^2 \, r_* \, \mathcal{H}_* \eta_\text{v}
        \left( \frac{a_*}{a_r} \right)^\frac{2\nu}{1 + \nu}
        \frac{1}{H_n R_*} \frac{d\mathcal{P}_\text{gw}}{d(H_n t)},$$
        :giombi_2026:`\ ` eq. 3.9a,
        where $\mathcal{H}_* \eta_\text{v} = \mathcal{H}_* \eta_* \Upsilon_\ell$ is the effective source lifetime,
        which is computed from the RMS fluid velocity $\bar{U}_f$ of the single-bubble fluid shell
        :py:attr:`bubble`, see :py:func:`pttools.ssm.scaling.H_star_eta_v`.

        :raises ValueError: if ``step_prev`` has not been given
        """
        spectrum = self.spectrum
        # The SSM spectrum is used only for the conversion factors, and therefore it's not computed.
        ssm = Spectrum(
            bubble=self.bubble, r_star=spectrum.r_star, y=spectrum.y, T_star=spectrum.T_star,
            g_star=spectrum.g_star, gs_star=spectrum.gs_star, compute=False)
        factor = ssm.r_star * ssm.H_star_eta_v * ssm.dilution_of_e
        return spectrum.F_gw0_h2(om_gamma0_h2=const.OMEGA_PHOTON_H2) * factor * spectrum.pow_gw_rate

    @tp.override
    def power_spectrum(
            self,
            f: FloatArr1D,
            noise: Noise | None = None,
            log_errors: bool = False) -> tuple[FloatArr1D, float]:
        r"""The simulated spectrum of :py:attr:`conversion` interpolated to the given frequencies, and its SNR.

        The spectrum is interpolated linearly in $\ln f$ below the lattice artifact, and it's zero elsewhere.

        :param f: frequencies $f$
        :param noise: noise curve, defaults to the default noise curve
        :param log_errors: unused, as the spectrum is not computed
        :return: $\Omega_{\text{gw},0} h^2$ and its SNR
        """
        match self.conversion:
            case LatticeConversion.ACCUMULATED:
                omgw0_h2, valid = self.omgw0_h2, self.valid
            case LatticeConversion.ASYMPTOTE:
                omgw0_h2, valid = self.omgw0_h2_asymptote, self.valid
            case LatticeConversion.RATE:
                omgw0_h2, valid = self.omgw0_h2_rate, self.valid_rate
        power_spectrum = np.interp(np.log(f), np.log(self.f[valid]), omgw0_h2[valid], left=0, right=0)
        return self.snr_and_store(f, power_spectrum, noise)

    @property
    def t_label(self) -> str:
        r"""Time of the spectrum in units of the shock formation time $t_\text{sh}$ as LaTeX math."""
        if not self.run.has_globals:
            return "t=?"
        return rf"t={self.spectrum.t / self.run.t_sh:.2f} \, t_\mathrm{{sh}}"

    @functools.cached_property
    def valid(self) -> slice:
        """Indices of the spectra below the lattice artifact.

        See :py:attr:`pttools.lattice.spectrum.LatticeSpectrum.valid_slice`.
        """
        return self.spectrum.valid_slice

    @functools.cached_property
    def valid_rate(self) -> slice:
        """Indices of :py:attr:`omgw0_h2_rate` below the lattice artifact, see :py:attr:`valid`."""
        return slice(None, lattice_artifact_start(self.spectrum.y, self.spectrum.pow_gw_rate))
