r"""
Lattice simulations and the engines
===================================

Compare the GW power spectra of the $4096^3$ hydrodynamic lattice simulations of :correia_2025:`\ `
with the spectra of the engines at the parameter values of the simulations.

The simulated spectra are those of the last time step of the data,
see :py:meth:`pttools.lattice.run_spectra.LatticeRunSpectra.last_step`,
which is also the last time step of the extrapolation of the GW power to late times,
as in the example ``examples.snr.singlets``.
They are converted to the GW power spectrum today from the GW power spectrum $\mathcal{P}_\text{gw}$
that has accumulated by the time step, scaled to the asymptotic GW power,
see :py:attr:`ptplot.science.spectrum.lattice.PowerSpectrumLattice.omgw0_h2_asymptote`.
The spectra converted from the GW power growth rate $\dot{\mathcal{P}}_\text{gw}$
(:py:attr:`ptplot.science.spectrum.lattice.PowerSpectrumLattice.omgw0_h2_rate`) are not drawn,
as the flow has decayed by the last time step,
and the growth rate is therefore small and noisy, and even negative at some wavenumbers.
The simulations are scale-free, as $H_n$ only enters through the Friedmann equation.
Therefore, $r_*$ is not taken from the simulations,
and the simulated spectra and the engines are evaluated at the same chosen value of $r_*$.

The SSM engine assumes exponential nucleation,
whereas the bubbles of the simulations are nucleated simultaneously,
see :py:attr:`pttools.lattice.run_base.LatticeRunBase.nuc_type`.
Exponential nucleation gives a wider distribution of bubble sizes,
which shifts the peak of the SSM spectrum to lower frequencies.
Therefore, the SSM spectrum with the nucleation type of the simulation is also drawn
when the SSM engine is enabled.

The simulated spectrum is drawn only below the lattice artifact at high $k$.
"""

import logging
from pathlib import Path
import typing as tp

from matplotlib import rc_context
from matplotlib.figure import Figure
from pttools.bubble import Bubble
from pttools.lattice import CHRW25_RUNS, LatticeRunParams, data_dir, load_chrw25_run
from pttools.omgw0 import Spectrum, SuppressionMethod
from pttools.ssm.nucleation import NucType
from pttools.ssm.suppression import DEFAULT_SUPPRESSION
from pttools.utils.time import log_duration

from examples.utils import save_and_show_figs
from ptplot.methods.generic import setup_logging
from ptplot.science import const
from ptplot.science.noise import Noise, resolve_noise
from ptplot.science.plot.lattice import lattice_curves
from ptplot.science.plot.ps import SpectrumCurve, power_spectrum_figure
from ptplot.science.spectrum import CHRW25_NAME, Engine, PowerSpectrumLattice, PowerSpectrumSSM, power_spectrum
from ptplot.science.type_hints import FloatArr1D

logger: logging.Logger = logging.getLogger(__name__)

#: $r_*$, Hubble-scaled mean bubble spacing at which the spectra are evaluated
R_STAR: float = 0.1
#: Line style of the SSM spectra with the nucleation type of the simulation
SSM_NUCLEATION_LINESTYLE: str = "-."
#: Abbreviations of the nucleation types in the labels
NUC_TYPE_LABELS: dict[NucType, str] = {NucType.EXPONENTIAL: "exp.", NucType.SIMULTANEOUS: "simult."}


def ssm_nucleation(
        bubble: Bubble,
        nuc_type: NucType,
        f: FloatArr1D,
        r_star: float = R_STAR,
        T_star: float = const.DEFAULT_T_STAR,
        g_star: float = const.DEFAULT_G_STAR) -> Spectrum:
    r"""SSM spectrum with the nucleation type of the simulation.

    The other settings, including the suppression, are the same as in
    :py:class:`ptplot.science.spectrum.ssm.PowerSpectrumSSM`.

    :param bubble: fluid shell with the parameters of the simulation
    :param nuc_type: nucleation type of the simulation, see :py:attr:`pttools.lattice.run_base.LatticeRunBase.nuc_type`
    :param f: frequencies $f$
    :param r_star: $r_*$, Hubble-scaled mean bubble spacing
    :param T_star: $T_*$, temperature at the time of GW production
    :param g_star: $g_*$, degrees of freedom
    :return: the spectrum
    """
    return Spectrum(
        bubble=bubble, f=f, r_star=r_star, T_star=T_star, g_star=g_star,
        nuc_type=nuc_type,
        suppression=DEFAULT_SUPPRESSION, suppression_method=SuppressionMethod.EXT_CONSTANT
    )


def plot_lattice(
        meta: LatticeRunParams,
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
    If the SSM engine is enabled, and the nucleation type of the simulation differs from the exponential nucleation
    of the SSM engine, the SSM spectrum with the nucleation type of the simulation is also drawn,
    see :py:func:`ssm_nucleation`.

    The simulated spectrum is that of the last time step of the data, see the description of this example.
    If ``asymptote`` is enabled, the simulated spectrum is scaled by
    $\Omega_\text{gw}^\infty / \Omega_\text{gw}(t)$,
    see :py:attr:`ptplot.science.spectrum.lattice.PowerSpectrumLattice.asymptote_ratio`.
    This assumes that the shape of the spectrum no longer changes after the time step.

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
    run = load_chrw25_run(meta.name, path=path)
    spectrum = PowerSpectrumLattice(run, r_star=r_star, T_star=T_star, g_star=g_star, name=CHRW25_NAME)
    bubble = spectrum.bubble
    logger.info("Plotting the power spectra of the %s run with r_star=%s.", run.name, r_star)
    if asymptote:
        logger.info("%s: Omega_gw^inf / Omega_gw(t) = %s", run.name, spectrum.asymptote_ratio)
    engines = Engine.engines(engine, strong=bool(engine))
    spectra = [
        power_spectrum(
            v_wall=run.v_wall, alpha=run.alpha_n, r_star=r_star,
            T_star=T_star, g_star=g_star, adiabatic_index=bubble.mean_adiabatic_index,
            engine=spectrum_engine
        )
        for spectrum_engine in engines
    ]
    curves = lattice_curves(spectrum, accumulated=not asymptote, asymptote=asymptote)
    if Engine.SSM in engines and run.nuc_type != NucType.EXPONENTIAL:
        ssm = ssm_nucleation(bubble, run.nuc_type, f=noise.f, r_star=r_star, T_star=T_star, g_star=g_star)
        curves.append(SpectrumCurve(
            f=noise.f, omgw0_h2=ssm.omgw0_h2(om_gamma0_h2=const.OMEGA_PHOTON_H2),
            label=rf"$\Omega_\mathrm{{sw}}$ (SSM, {NUC_TYPE_LABELS[run.nuc_type]})",
            color=PowerSpectrumSSM.COLOR, linestyle=SSM_NUCLEATION_LINESTYLE
        ))
    fig = power_spectrum_figure(
        spectra, noise=noise, curves=curves, title=rf"{meta.label_latex}, $r_*={r_star}$")

    ax = fig.axes[0]
    # The SSM engine uses exponential nucleation, which is marked to distinguish it from that of the simulation.
    for line in ax.get_lines():
        line.set_label(str(line.get_label()).replace(
            f"({PowerSpectrumSSM.SHORT_NAME})",
            f"({PowerSpectrumSSM.SHORT_NAME}, {NUC_TYPE_LABELS[NucType.EXPONENTIAL]})"))
    with rc_context(const.DEFAULT_RC_CONTEXT):
        # The labels are longer than in the other power spectrum figures, so a smaller font is used.
        ax.legend(loc="lower left", fontsize="small")
    return fig


@log_duration
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
        for name, meta in CHRW25_RUNS.items()
    })


if __name__ == "__main__":
    main()
