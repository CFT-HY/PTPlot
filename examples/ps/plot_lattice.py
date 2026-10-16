r"""
Lattice simulations and the engines
===================================

Compare the GW power spectra of the $4096^3$ hydrodynamic lattice simulations of :correia_2025:`\ `
with the spectra of the engines at the parameter values of the simulations.

The simulations are in flat space, and their GW power spectrum grows linearly in time.
The simulated growth rate is therefore converted to the GW power spectrum today
with the same factors for the source lifetime and the expansion of the universe
as in the Sound Shell Model, see :py:func:`lattice_omgw0_h2`.
The simulations are scale-free, as $H_n$ only enters through the Friedmann equation.
Therefore, $r_*$ is not taken from the simulations,
and the simulated spectra and the engines are evaluated at the same chosen value of $r_*$.

The simulated spectrum is drawn only above the lowest bins and below the lattice artifact at high $k$.
The data of the simulations is required for this example, see :py:mod:`pttools.lattice.correia_2025`.
"""

import logging
from pathlib import Path
import typing as tp

from matplotlib import rc_context
from matplotlib.figure import Figure
from pttools.bubble import Bubble
from pttools.lattice import CORREIA_2025_RUNS, CorreiaRun, LatticeSpectrum, data_dir, load_correia_2025_run
from pttools.omgw0 import Spectrum
from pttools.ssm.suppression.fit import lattice_artifact_start
from pttools.utils.formatting import as_latex

from examples.utils import save_and_show_figs
from ptplot.methods.generic import setup_logging
from ptplot.science import const
from ptplot.science.noise import Noise, resolve_noise
from ptplot.science.plot.ps import power_spectrum_figure
from ptplot.science.spectrum import BAG, Engine, PowerSpectrum, power_spectrum
from ptplot.science.type_hints import FloatArr1D

logger: logging.Logger = logging.getLogger(__name__)

#: $r_*$, Hubble-scaled mean bubble spacing at which the spectra are evaluated
R_STAR: float = 0.1
#: Smallest $z = kR_*$ of the simulated spectra to plot. This excludes the lowest bin, which contains only one mode.
Y_MIN: float = 2.
#: Color of the simulated spectra
LATTICE_COLOR: str = "black"


def lattice_omgw0_h2(
        spectrum: LatticeSpectrum,
        bubble: Bubble,
        r_star: float = R_STAR,
        T_star: float = const.DEFAULT_T_STAR,
        g_star: float = const.DEFAULT_G_STAR) -> tuple[FloatArr1D, FloatArr1D]:
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
    The frequencies are
    $$f = \frac{z}{r_*} f_{\ast,0},$$
    :gowling_2021:`\ ` eq. 2.12.

    :param spectrum: simulated spectrum
    :param bubble: fluid shell with the parameters of the simulation
    :param r_star: $r_*$, Hubble-scaled mean bubble spacing
    :param T_star: $T_*$, temperature at the time of GW production
    :param g_star: $g_*$, degrees of freedom
    :return: $f$ and $\Omega_{\text{gw},0} h^2$
    """
    # The SSM spectrum is used only for the conversion factors, and therefore it's not computed.
    ssm = Spectrum(bubble=bubble, r_star=r_star, y=spectrum.y, T_star=T_star, g_star=g_star, compute=False)
    factor = ssm.r_star * ssm.H_star_eta_v * ssm.dilution_of_e
    omgw0_h2 = ssm.F_gw0_h2(om_gamma0_h2=const.OMEGA_PHOTON_H2) * factor * spectrum.pow_gw_rate
    return ssm.f(z=spectrum.y), omgw0_h2


def plot_lattice(
        meta: CorreiaRun,
        path: Path,
        engine: Engine | str | tp.Iterable[Engine] | None = None,
        r_star: float = R_STAR,
        T_star: float = const.DEFAULT_T_STAR,
        g_star: float = const.DEFAULT_G_STAR,
        noise: Noise | None = None) -> Figure:
    r"""Plot the simulated GW power spectrum together with the spectra of the engines.

    The engines are given $v_\text{wall}$ and $\alpha_n$ of the simulation, and $r_*$.
    The mean adiabatic index $\Gamma$ is that of the bag model fluid shell with these parameters,
    as used by the Sound Shell Model.

    :param meta: metadata of the simulation run
    :param path: root directory of the data
    :param engine: engine or engines to model the spectrum with, defaults to all engines
    :param r_star: $r_*$, Hubble-scaled mean bubble spacing
    :param T_star: $T_*$, temperature at the time of GW production
    :param g_star: $g_*$, degrees of freedom
    :param noise: which noise curve to use
    :return: power spectrum figure
    """
    noise = resolve_noise(noise)
    run = load_correia_2025_run(meta.name, path=path)
    bubble = Bubble(model=BAG, v_wall=run.v_wall, alpha_n=run.alpha_n)
    logger.info("Plotting the power spectra of the %s run with r_star=%s.", run.name, r_star)
    spectra = [
        power_spectrum(
            v_wall=run.v_wall, alpha=run.alpha_n, r_star=r_star,
            T_star=T_star, g_star=g_star, adiabatic_index=bubble.mean_adiabatic_index,
            engine=spectrum_engine
        )
        for spectrum_engine in Engine.engines(engine)
    ]
    fig = power_spectrum_figure(
        spectra, noise=noise, title=rf"{meta.label_latex}, $r_*={r_star}$")

    spectrum = run.spectrum(meta.step, meta.step_prev)
    f, omgw0_h2 = lattice_omgw0_h2(spectrum, bubble=bubble, r_star=r_star, T_star=T_star, g_star=g_star)
    valid = spectrum.y >= Y_MIN
    i_artifact = lattice_artifact_start(spectrum.y, spectrum.pow_gw_rate)
    if i_artifact is not None:
        valid[i_artifact:] = False
    snr = PowerSpectrum.snr(f=f[valid], power_spectrum=omgw0_h2[valid], noise=noise)

    ax = fig.axes[0]
    with rc_context(const.DEFAULT_RC_CONTEXT):
        ax.plot(
            f[valid], omgw0_h2[valid], color=LATTICE_COLOR,
            label=rf"$\Omega_\mathrm{{sw}}$ (sim., $t={spectrum.t / run.t_sh:.2f} \, t_\mathrm{{sh}}$), "
                  f"SNR={as_latex(snr, math_mode=True)}"
        )
        ax.legend(loc="upper right")
    return fig


def main() -> None:
    """Plot the spectra of the simulations of Correia et al. and of the engines."""
    setup_logging()
    path = data_dir()
    if path is None:
        logger.warning("The data of Correia et al. was not found. Skipping the example.")
        return
    engines = Engine.engines(log=True)
    save_and_show_figs({
        f"lattice_{name}_ps": plot_lattice(meta, path=path, engine=engines)
        for name, meta in CORREIA_2025_RUNS.items()
    })


if __name__ == "__main__":
    main()
