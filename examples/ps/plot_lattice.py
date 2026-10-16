r"""
Lattice simulations and the engines
===================================

Compare the GW power spectra of the $4096^3$ hydrodynamic lattice simulations of :correia_2025:`\ `
with the spectra of the engines at the parameter values of the simulations.

The simulated GW power spectra are converted to the GW power spectrum today in two ways:

- From the GW power spectrum $\mathcal{P}_\text{gw}$ that has accumulated by the time step,
  as in PTtools, see :py:class:`pttools.lattice.spectrum.LatticeSpectrum`.
  The simulations end before the GW power has stopped growing.
  Therefore, the spectrum is scaled to the asymptotic GW power,
  which is extrapolated with :correia_2025:`\ ` eq. 47,
  see :py:meth:`pttools.lattice.spectrum.LatticeSpectrum.omega_gw_asymptote_ratio`.
  This conversion neglects the expansion of the universe.
- From the GW power growth rate $\dot{\mathcal{P}}_\text{gw}$ at the time step,
  with the source lifetime and the expansion of the universe of the Sound Shell Model,
  see :py:func:`lattice_omgw0_h2_rate`.
  This is how PTtools compares the simulations with the SSM,
  e.g. in the example ``lattice_spectra`` of PTtools.

The accumulated GW power includes the earlier times, when the flow was at smaller scales,
and therefore it peaks at higher frequencies than the growth rate.
The simulations are scale-free, as $H_n$ only enters through the Friedmann equation.
Therefore, $r_*$ is not taken from the simulations,
and the simulated spectra and the engines are evaluated at the same chosen value of $r_*$.

The SSM engine assumes exponential nucleation,
whereas the bubbles of the simulations are nucleated simultaneously.
Exponential nucleation gives a wider distribution of bubble sizes,
which shifts the peak of the SSM spectrum to lower frequencies.
Therefore, the SSM spectrum with simultaneous nucleation is also drawn when the SSM engine is enabled.

The simulated spectrum is drawn only below the lattice artifact at high $k$.
"""

import logging
from pathlib import Path
import typing as tp

from matplotlib import rc_context
from matplotlib.figure import Figure
from pttools.bubble import Bubble
from pttools.lattice import CORREIA_2025_RUNS, CorreiaRun, LatticeSpectrum, data_dir, load_correia_2025_run
from pttools.omgw0 import Spectrum, SuppressionMethod
from pttools.ssm.nucleation import NucType
from pttools.ssm.suppression import DEFAULT_SUPPRESSION
from pttools.ssm.suppression.fit import lattice_artifact_start
from pttools.utils.formatting import as_latex

from examples.utils import save_and_show_figs
from ptplot.methods.generic import setup_logging
from ptplot.science import const
from ptplot.science.noise import Noise, resolve_noise
from ptplot.science.plot.ps import power_spectrum_figure
from ptplot.science.spectrum import BAG, Engine, PowerSpectrum, PowerSpectrumSSM, power_spectrum
from ptplot.science.type_hints import FloatArr1D

logger: logging.Logger = logging.getLogger(__name__)

#: $r_*$, Hubble-scaled mean bubble spacing at which the spectra are evaluated
R_STAR: float = 0.1
#: Color of the simulated spectra
LATTICE_COLOR: str = "black"
#: Color of the simulated spectra converted from the GW power growth rate
LATTICE_RATE_COLOR: str = "grey"
#: Line style of the simulated spectra
LATTICE_LINESTYLE: str = ":"
#: Line style of the SSM spectra with simultaneous nucleation
SSM_SIMULTANEOUS_LINESTYLE: str = "-."


def ssm_simultaneous(
        bubble: Bubble,
        f: FloatArr1D,
        r_star: float = R_STAR,
        T_star: float = const.DEFAULT_T_STAR,
        g_star: float = const.DEFAULT_G_STAR) -> Spectrum:
    r"""SSM spectrum with simultaneous nucleation, as in the simulations.

    The other settings, including the suppression, are the same as in
    :py:class:`ptplot.science.spectrum.ssm.PowerSpectrumSSM`.

    :param bubble: fluid shell with the parameters of the simulation
    :param f: frequencies $f$
    :param r_star: $r_*$, Hubble-scaled mean bubble spacing
    :param T_star: $T_*$, temperature at the time of GW production
    :param g_star: $g_*$, degrees of freedom
    :return: the spectrum
    """
    return Spectrum(
        bubble=bubble, f=f, r_star=r_star, T_star=T_star, g_star=g_star,
        nuc_type=NucType.SIMULTANEOUS,
        suppression=DEFAULT_SUPPRESSION, suppression_method=SuppressionMethod.EXT_CONSTANT
    )


def lattice_omgw0_h2_rate(spectrum: LatticeSpectrum, bubble: Bubble) -> FloatArr1D:
    r"""$\Omega_{\text{gw},0} h^2(f)$, GW power spectrum today from the simulated GW power growth rate.

    The simulated growth rate is scaled with the same factors as the Sound Shell Model of PTtools,
    :py:func:`pttools.ssm.spec_den_gw.spec_den_gw_scaling`,
    $$\Omega_{\text{gw},0} h^2(f) = F_{\text{gw},0} h^2 \, r_* \, \mathcal{H}_* \eta_\text{v}
    \left( \frac{a_*}{a_r} \right)^\frac{2\nu}{1 + \nu}
    \frac{1}{H_n R_*} \frac{d\mathcal{P}_\text{gw}}{d(H_n t)},$$
    :giombi_2026:`\ ` eq. 3.9a,
    where $\mathcal{H}_* \eta_\text{v} = \mathcal{H}_* \eta_* \Upsilon_\ell$ is the effective source lifetime,
    which is computed from the RMS fluid velocity $\bar{U}_f$ of the single-bubble fluid shell,
    see :py:func:`pttools.ssm.scaling.H_star_eta_v`.
    The frequencies are those of the spectrum, :py:meth:`pttools.omgw0.base.Omgw0Base.f`.

    :param spectrum: simulated spectrum, which gives $r_*$, $T_*$ and $g_*$
    :param bubble: fluid shell with the parameters of the simulation
    :return: $\Omega_{\text{gw},0} h^2$
    """
    # The SSM spectrum is used only for the conversion factors, and therefore it's not computed.
    ssm = Spectrum(
        bubble=bubble, r_star=spectrum.r_star, y=spectrum.y, T_star=spectrum.T_star, g_star=spectrum.g_star,
        gs_star=spectrum.gs_star, compute=False)
    factor = ssm.r_star * ssm.H_star_eta_v * ssm.dilution_of_e
    return spectrum.F_gw0_h2(om_gamma0_h2=const.OMEGA_PHOTON_H2) * factor * spectrum.pow_gw_rate


def plot_lattice(
        meta: CorreiaRun,
        path: Path,
        engine: Engine | str | tp.Iterable[Engine] | None = None,
        r_star: float = R_STAR,
        T_star: float = const.DEFAULT_T_STAR,
        g_star: float = const.DEFAULT_G_STAR,
        noise: Noise | None = None,
        asymptote: bool = True) -> Figure:
    r"""Plot the simulated GW power spectrum together with the spectra of the engines.

    The engines are given $v_\text{wall}$ and $\alpha_n$ of the simulation, and $r_*$.
    The mean adiabatic index $\Gamma$ is that of the bag model fluid shell with these parameters,
    as used by the Sound Shell Model.
    If the SSM engine is enabled, the SSM spectrum with simultaneous nucleation is also drawn,
    see :py:func:`ssm_simultaneous`.

    The simulated spectrum is drawn with both conversions, see the description of this example.
    If ``asymptote`` is enabled, the simulated spectrum at the time step of ``meta`` is scaled by
    $\Omega_\text{gw}^\infty / \Omega_\text{gw}(t)$,
    see :py:meth:`pttools.lattice.spectrum.LatticeSpectrum.omega_gw_asymptote_ratio`.
    This assumes that the shape of the spectrum no longer changes after that time step.

    :param meta: metadata of the simulation run
    :param path: root directory of the data
    :param engine: engine or engines to model the spectrum with,
        defaults to all engines except those for strong transitions only
    :param r_star: $r_*$, Hubble-scaled mean bubble spacing
    :param T_star: $T_*$, temperature at the time of GW production
    :param g_star: $g_*$, degrees of freedom
    :param noise: which noise curve to use
    :param asymptote: whether to extrapolate the accumulated simulated GW power to late times
    :return: power spectrum figure
    """
    noise = resolve_noise(noise)
    run = load_correia_2025_run(meta.name, path=path)
    bubble = Bubble(model=BAG, v_wall=run.v_wall, alpha_n=run.alpha_n)
    logger.info("Plotting the power spectra of the %s run with r_star=%s.", run.name, r_star)
    engines = Engine.engines(engine, strong=bool(engine))
    spectra = [
        power_spectrum(
            v_wall=run.v_wall, alpha=run.alpha_n, r_star=r_star,
            T_star=T_star, g_star=g_star, adiabatic_index=bubble.mean_adiabatic_index,
            engine=spectrum_engine
        )
        for spectrum_engine in engines
    ]
    fig = power_spectrum_figure(
        spectra, noise=noise, title=rf"{meta.label_latex}, $r_*={r_star}$")

    spectrum = run.spectrum(meta.step, meta.step_prev, r_star=r_star, T_star=T_star, g_star=g_star)
    f = spectrum.f()
    omgw0_h2 = spectrum.omgw0_h2(om_gamma0_h2=const.OMEGA_PHOTON_H2)
    if asymptote:
        ratio = spectrum.omega_gw_asymptote_ratio()
        logger.info("%s: Omega_gw^inf / Omega_gw(t) = %s", run.name, ratio)
        omgw0_h2 = ratio * omgw0_h2
        time_label = r"t \to \infty"
    else:
        time_label = rf"t={spectrum.t / run.t_sh:.2f} \, t_\mathrm{{sh}}"
    valid = slice(None, lattice_artifact_start(spectrum.y, spectrum.pow_gw))
    snr = PowerSpectrum.snr(f=f[valid], power_spectrum=omgw0_h2[valid], noise=noise)
    omgw0_h2_rate = lattice_omgw0_h2_rate(spectrum, bubble)
    valid_rate = slice(None, lattice_artifact_start(spectrum.y, spectrum.pow_gw_rate))
    snr_rate = PowerSpectrum.snr(f=f[valid_rate], power_spectrum=omgw0_h2_rate[valid_rate], noise=noise)

    ax = fig.axes[0]
    # The SSM engine uses exponential nucleation, which is marked to distinguish it from simultaneous nucleation.
    for line in ax.get_lines():
        line.set_label(str(line.get_label()).replace(
            f"({PowerSpectrumSSM.SHORT_NAME})", f"({PowerSpectrumSSM.SHORT_NAME}, exp.)"))
    with rc_context(const.DEFAULT_RC_CONTEXT):
        if Engine.SSM in engines:
            ssm = ssm_simultaneous(bubble, f=noise.f, r_star=r_star, T_star=T_star, g_star=g_star)
            omgw0_h2_ssm = ssm.omgw0_h2(om_gamma0_h2=const.OMEGA_PHOTON_H2)
            snr_ssm = PowerSpectrum.snr(f=noise.f, power_spectrum=omgw0_h2_ssm, noise=noise)
            ax.plot(
                noise.f, omgw0_h2_ssm, color=PowerSpectrumSSM.COLOR, linestyle=SSM_SIMULTANEOUS_LINESTYLE,
                label=r"$\Omega_\mathrm{sw}$ (SSM, simult.), " f"SNR={as_latex(snr_ssm, math_mode=True)}"
            )
        ax.plot(
            f[valid], omgw0_h2[valid], color=LATTICE_COLOR, linestyle=LATTICE_LINESTYLE,
            label=rf"$\Omega_\mathrm{{sw}}$ (CHRW25sim, $\mathcal{{P}}_\mathrm{{gw}}$, ${time_label}$), "
                  f"SNR={as_latex(snr, math_mode=True)}"
        )
        ax.plot(
            f[valid_rate], omgw0_h2_rate[valid_rate], color=LATTICE_RATE_COLOR, linestyle=LATTICE_LINESTYLE,
            label=rf"$\Omega_\mathrm{{sw}}$ (CHRW25sim, $\dot{{\mathcal{{P}}}}_\mathrm{{gw}}$), "
                  f"SNR={as_latex(snr_rate, math_mode=True)}"
        )
        # The labels are longer than in the other power spectrum figures, so a smaller font is used.
        ax.legend(loc="lower left", fontsize="small")
    return fig


def main() -> None:
    """Plot the spectra of the simulations of Correia et al. and of the engines."""
    setup_logging()
    path = data_dir()
    if path is None:
        logger.warning("The data of Correia et al. was not found. Skipping the example.")
        return
    engines = Engine.engines(log=True, strong=False)
    save_and_show_figs({
        f"lattice_{name}_ps": plot_lattice(meta, path=path, engine=engines)
        for name, meta in CORREIA_2025_RUNS.items()
    })


if __name__ == "__main__":
    main()
