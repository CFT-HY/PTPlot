"""Tests for the GW power spectra of lattice simulations.

The reference values were computed with the code of the example ``examples.ps.plot_lattice``
before it was moved to :py:mod:`ptplot.science.spectrum.lattice`.
At that time, PTtools did not yet take into account the expansion of the universe in
:py:attr:`pttools.lattice.spectrum.LatticeSpectrum.pow_gw`, and therefore the reference values of the spectra
from the accumulated GW power are those of flat space, which are multiplied by the expansion factor in the tests.
The tests are skipped if the data of the simulations is not available.
"""

import functools
import typing as tp

import numpy as np
from pttools.lattice import CHRW25_RUNS, LatticeRun, load_chrw25_runs
import pytest

from ptplot.science import const
from ptplot.science.noise import resolve_noise
from ptplot.science.spectrum import LatticeConversion, PowerSpectrum, PowerSpectrumLattice

#: $r_*$ of the reference values
R_STAR: float = 0.1
#: Reference values of each run at the time steps of :py:attr:`pttools.lattice.params.LatticeRunParams.fig_step`
#: and ``fig_step_prev``:
#: the last time step of the data,
#: $\Omega_\text{gw}^\infty / \Omega_\text{gw}(t)$ with the fit ending at the last time step of the data,
#: the peak of $\Omega_{\text{gw},0} h^2$ in flat space and its frequency,
#: the peak of $\Omega_{\text{gw},0} h^2$ from the growth rate and its frequency,
#: the indices of the lattice artifacts in the spectrum and in the growth rate,
#: and the values at the index 10 of the spectrum and of the spectrum from the growth rate
REFERENCE: dict[str, dict[str, tp.Any]] = {
    "detonation": {
        "last_step": 24800,
        "ratio": 2.0035471331855126,
        "peak": (0.00040828135325580485, 8.360978692902261e-11),
        "peak_rate": (0.0003340483799365676, 4.6955575666344826e-11),
        "artifact": (1044, 655),
        "index_10": (3.331878438691251e-11, 2.1623697173381516e-12),
    },
    "deflagration": {
        "last_step": 40000,
        "ratio": 1.7212260897585658,
        "peak": (0.00025981540661733035, 2.7436925465918576e-11),
        "peak_rate": (0.0001855824332980931, 1.5186492752418865e-11),
        "artifact": (485, 474),
        "index_10": (3.68985172323764e-12, 1.2772120727174358e-12),
    },
}


@functools.cache
def runs() -> dict[str, LatticeRun]:
    """The lattice simulations of Correia et al., or an empty dict if the data is not available."""
    return load_chrw25_runs(missing_ok=True)


def spectrum(name: str) -> PowerSpectrumLattice:
    """The spectrum of a run at the time steps of the reference values."""
    if not runs():
        pytest.skip("The data of the lattice simulations is not available.")
    meta = CHRW25_RUNS[name]
    return PowerSpectrumLattice(runs()[name], meta.fig_step, meta.fig_step_prev, r_star=R_STAR)


def expansion_factor(s: PowerSpectrumLattice) -> float:
    r"""$\eta_\text{v} / \Delta \eta_\text{v}$ of the source duration $t / R_*$ for radiation domination ($\nu = 0$).

    $$\frac{\eta_\text{v}}{\Delta \eta_\text{v}} = \frac{1}{1 + r_* t / R_*},$$
    see :py:attr:`pttools.lattice.spectrum.LatticeSpectrum.expansion_factor`.
    """
    return 1 / (1 + s.r_star * s.spectrum.t / s.run.R_star)


@pytest.mark.parametrize("name", list(REFERENCE))
def test_reference(name: str) -> None:
    """The spectra should agree with the reference values."""
    ref = REFERENCE[name]
    s = spectrum(name)
    assert s.step == CHRW25_RUNS[name].fig_step
    assert s.step_end == ref["last_step"]
    assert (s.r_star, s.T_star, s.g_star) == pytest.approx((R_STAR, const.DEFAULT_T_STAR, const.DEFAULT_G_STAR))
    # The expansion factor is 0.70-0.74 for these time steps at r_* = 0.1.
    factor = expansion_factor(s)
    assert s.spectrum.expansion_factor * s.spectrum.dilution_of_e == pytest.approx(factor, rel=1e-12, abs=0)
    (f_peak, peak), (f_peak_rate, peak_rate) = ref["peak"], ref["peak_rate"]
    for omgw0_h2, f_ref, peak_ref in ((s.omgw0_h2, f_peak, factor * peak), (s.omgw0_h2_rate, f_peak_rate, peak_rate)):
        i_max = np.nanargmax(omgw0_h2)
        assert (s.f[i_max], omgw0_h2[i_max]) == pytest.approx((f_ref, peak_ref), rel=1e-10, abs=0)
    index_10, index_10_rate = ref["index_10"]
    assert (s.omgw0_h2[10], s.omgw0_h2_rate[10]) == pytest.approx((factor * index_10, index_10_rate), rel=1e-10, abs=0)
    assert (s.valid, s.valid_rate) == (slice(None, ref["artifact"][0]), slice(None, ref["artifact"][1]))


@pytest.mark.parametrize("name", list(REFERENCE))
def test_asymptote(name: str) -> None:
    r"""The asymptotic spectrum should be scaled by the asymptote and the expansion of the universe.

    The ratio of the asymptotic and current GW energy density is
    $R = \Omega_\text{gw}^\infty / \Omega_\text{gw}(t)$.
    With the duration of the time step, the ratio is that of the simulation.
    With the duration $\Delta \tau_\text{v}^\infty = R \, t / R_*$ of the asymptote,
    the ratio is
    $$R \frac{1 + r_* t / R_*}{1 + r_* R \, t / R_*}$$ for radiation domination.
    """
    if not runs():
        pytest.skip("The data of the lattice simulations is not available.")
    meta = CHRW25_RUNS[name]
    ratio = REFERENCE[name]["ratio"]
    for asymptote_duration in (False, True):
        s = PowerSpectrumLattice(
            runs()[name], meta.fig_step, meta.fig_step_prev, r_star=R_STAR, asymptote_duration=asymptote_duration
        )
        r_tau = s.r_star * s.spectrum.t / s.run.R_star
        expected = ratio * (1 + r_tau) / (1 + ratio * r_tau) if asymptote_duration else ratio
        assert s.asymptote_ratio == pytest.approx(expected, rel=1e-10, abs=0)
        np.testing.assert_allclose(s.omgw0_h2_asymptote, expected * s.omgw0_h2, rtol=1e-10, atol=0)


def test_defaults() -> None:
    """The time step and the end of the fit should default to the last time step of the data."""
    if not runs():
        pytest.skip("The data of the lattice simulations is not available.")
    s = PowerSpectrumLattice(runs()["detonation"])
    assert s.step == s.step_end == REFERENCE["detonation"]["last_step"]
    assert s.r_star == pytest.approx(s.run.r_star)
    assert s.name == "lattice"
    with pytest.raises(ValueError, match="step_prev"):
        _ = s.omgw0_h2_rate


@pytest.mark.parametrize("name", list(REFERENCE))
def test_base_class(name: str) -> None:
    """The parameters of the base class should be those of the simulation."""
    s = spectrum(name)
    assert isinstance(s, PowerSpectrum)
    run = runs()[name]
    assert (s.v_wall, s.alpha, s.r_star) == pytest.approx((run.v_wall, run.alpha_n, R_STAR))
    assert s.adiabatic_index == pytest.approx(s.bubble.mean_adiabatic_index)
    assert s.beta_tilde > 0
    assert s.ubarf > 0


@pytest.mark.parametrize("conversion", list(LatticeConversion))
def test_power_spectrum(conversion: LatticeConversion) -> None:
    """The spectrum of the conversion should be interpolated below the lattice artifact, and be zero elsewhere."""
    s = spectrum("detonation")
    s.conversion = conversion
    omgw0_h2, valid = {
        LatticeConversion.ACCUMULATED: (s.omgw0_h2, s.valid),
        LatticeConversion.ASYMPTOTE: (s.omgw0_h2_asymptote, s.valid),
        LatticeConversion.RATE: (s.omgw0_h2_rate, s.valid_rate),
    }[conversion]
    f_valid = s.f[valid]
    # At the frequencies of the simulation, the interpolation gives the simulated values.
    np.testing.assert_allclose(s.power_spectrum(f_valid)[0], omgw0_h2[valid], rtol=1e-10)
    # Outside the valid range, the spectrum is zero.
    outside = np.array([f_valid[0] / 2, f_valid[-1] * 2])
    np.testing.assert_array_equal(s.power_spectrum(outside)[0], [0, 0])
    noise = resolve_noise(None)
    power_spectrum, snr = s.power_spectrum(noise.f, noise=noise)
    assert snr == pytest.approx(PowerSpectrum.snr(noise.f, power_spectrum, noise))
    assert snr > 0
    assert s.last_snr == snr
