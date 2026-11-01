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
that has accumulated by the time step (faded), and scaled to the asymptotic GW power,
see :py:attr:`ptplot.science.spectrum.lattice.PowerSpectrumLattice.omgw0_h2` and
:py:attr:`ptplot.science.spectrum.lattice.PowerSpectrumLattice.omgw0_h2_asymptote`.
The spectra converted from the GW power growth rate $\dot{\mathcal{P}}_\text{gw}$
(:py:attr:`ptplot.science.spectrum.lattice.PowerSpectrumLattice.omgw0_h2_rate`) are not drawn,
as the flow has decayed by the last time step,
and the growth rate is therefore small and noisy, and even negative at some wavenumbers.
The simulations are scale-free, as $H_n$ only enters through the Friedmann equation.
Therefore, $r_*$ is not taken from the simulations,
and the simulated spectra and the engines are evaluated at the same chosen value of $r_*$.

The SSM engine assumes exponential nucleation (faded),
whereas the bubbles of the simulations are nucleated simultaneously,
see :py:attr:`pttools.lattice.run_base.LatticeRunBase.nuc_type`.
Exponential nucleation gives a wider distribution of bubble sizes,
which shifts the peak of the SSM spectrum to lower frequencies.
Therefore, the SSM spectrum with simultaneous nucleation is also drawn when the SSM engine is enabled.

The simulated spectrum is drawn only below the lattice artifact at high $k$.
The figures are drawn with :py:mod:`ptplot.science.plot.lattice`, in the same style as those of
``examples.snr.singlets``. The figures with the suffix ``_paper`` have no title and no SNRs in the legend.
The SNRs are saved as CSV files in the directory ``csv``, with the same names as the figures.
"""

import logging
from pathlib import Path
import typing as tp

from pttools.lattice import CHRW25_RUNS, LatticeRunParams, data_dir, load_chrw25_run
from pttools.utils.time import log_duration

from examples.utils import csv_path, save_and_show_figs
from ptplot.methods.generic import setup_logging
from ptplot.science import const
from ptplot.science.noise import Noise
from ptplot.science.plot.lattice import LatticeComparison, lattice_comparison
from ptplot.science.spectrum import CHRW25_NAME, Engine, PowerSpectrumLattice, power_spectrum

logger: logging.Logger = logging.getLogger(__name__)

#: $r_*$, Hubble-scaled mean bubble spacing at which the spectra are evaluated
R_STAR: float = 0.1


def compare_lattice(
        meta: LatticeRunParams,
        path: Path,
        engine: Engine | str | tp.Iterable[Engine] | None = None,
        r_star: float = R_STAR,
        T_star: float = const.DEFAULT_T_STAR,
        g_star: float = const.DEFAULT_G_STAR,
        noise: Noise | None = None) -> LatticeComparison:
    r"""Compare the simulated GW power spectrum to the spectra of the engines.

    The engines are given $v_\text{wall}$ and $\alpha_n$ of the simulation, and $r_*$.
    The mean adiabatic index $\Gamma$ is that of the bag model fluid shell with these parameters,
    as used by the Sound Shell Model.
    The SSM spectrum is drawn with both exponential and simultaneous nucleation,
    see :py:func:`ptplot.science.plot.lattice.ssm_curves`.

    The simulated spectrum is that of the last time step of the data, see the description of this example.
    It is drawn both as it is, and scaled by $\Omega_\text{gw}^\infty / \Omega_\text{gw}(t)$,
    see :py:attr:`ptplot.science.spectrum.lattice.PowerSpectrumLattice.asymptote_ratio`.
    The latter assumes that the shape of the spectrum no longer changes after the time step.

    :param meta: metadata of the simulation run
    :param path: root directory of the data
    :param engine: engine or engines to model the spectrum with,
        defaults to all engines except those for strong transitions only
    :param r_star: $r_*$, Hubble-scaled mean bubble spacing
    :param T_star: $T_*$, temperature at the time of GW production
    :param g_star: $g_*$, degrees of freedom
    :param noise: which noise curve to use
    :return: the comparison, from which the figures can be drawn
    """
    run = load_chrw25_run(meta.name, path=path)
    spectrum = PowerSpectrumLattice(run, r_star=r_star, T_star=T_star, g_star=g_star, name=CHRW25_NAME)
    logger.info("Plotting the power spectra of the %s run with r_star=%s.", run.name, r_star)
    logger.info("%s: Omega_gw^inf / Omega_gw(t) = %s", run.name, spectrum.asymptote_ratio)
    spectra = [
        power_spectrum(
            v_wall=run.v_wall, alpha=run.alpha_n, r_star=r_star,
            T_star=T_star, g_star=g_star, adiabatic_index=spectrum.bubble.mean_adiabatic_index,
            engine=spectrum_engine
        )
        for spectrum_engine in Engine.engines(engine, strong=bool(engine))
    ]
    return lattice_comparison(spectrum, spectra, noise=noise, title=rf"{meta.label_latex}, $r_*={r_star}$")


@log_duration
def main() -> None:
    """Plot the spectra of the simulations of Correia et al. and of the engines."""
    setup_logging()
    path = data_dir()
    if path is None:
        logger.warning("The data of Correia et al. was not found. Skipping the example.")
        return
    engines = Engine.engines(log=True, strong=False)
    figs = {}
    for name, meta in CHRW25_RUNS.items():
        fig_name = f"lattice_{name}_ps"
        comparison = compare_lattice(meta, path=path, engine=engines)
        comparison.save_csv(csv_path(fig_name))
        figs[fig_name] = comparison.figure()
        figs[f"{fig_name}_paper"] = comparison.figure(title=False, snr=False)
    save_and_show_figs(figs)


if __name__ == "__main__":
    main()
