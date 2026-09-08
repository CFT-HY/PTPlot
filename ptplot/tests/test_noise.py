r"""Tests for the noise curves.

PTPlot used to ship precomputed LISA sensitivity curves as text files in
:py:mod:`ptplot.science.sensitivity`, and now uses
:py:func:`pttools.omgw0.noise.omega_noise_h2` instead.
These tests document how the two are related.

Which conventions are correct
-----------------------------
The ones that PTtools uses, i.e. those of :smith_2019:`\ `:

- The total noise is
  $\Omega_\text{noise} h^2 = (\Omega_\text{ins} + \Omega_\text{eb} + \Omega_\text{gb}) h^2$
  (:gowling_2021:`\ ` eq. 3.13), where the compact binary noises may be left out
  if the individual binaries are assumed to be resolved and subtracted.
- The LISA instrument noise is that of the noise-orthogonal A and E TDI channels,
  $S_A = S_E \approx \frac{40}{3} ({P}_\text{oms} + 4 {P}_\text{acc})
  \left( 1 + \left( \frac{3f}{4f_t} \right)^2 \right)$
  (:smith_2019:`\ ` eq. 63, :py:func:`pttools.omgw0.noise.S_AE_approx`).
- Observing with $N_c$ independent channels of equal noise improves the SNR by $\sqrt{N_c}$,
  which is equivalent to dividing the noise by $\sqrt{N_c}$.
  LISA has two such channels, so the factor is $\frac{1}{\sqrt{2}}$
  (:smith_2019:`\ ` eq. 59, :py:func:`pttools.omgw0.noise.S_AE`).
  :gowling_2023:`\ ` eq. 3.9 instead keeps the factor of $N_c = 2$ inside the SNR integral,
  which gives the same result.
- The conversion from a one-sided noise power spectral density to the fractional GW energy
  density is $\Omega h^2 = \frac{4 \pi^2}{3 H_{100}^2} f^3 S(f)$
  (:smith_2019:`\ ` eq. 59, :maggiore_1999:`\ ` eq. 18, :lisa_conventions:`\ ` eq. 167,
  :gowling_2021:`\ ` eq. 3.8, :py:func:`pttools.omgw0.noise.omega_h2`).
  :caprini_2020:`\ ` eq. 34 has $2 \pi^2$ instead.

The last point is the one that matters most in practice, since
:py:func:`pttools.omgw0.noise.signal_to_noise_ratio` computes
$\rho = \sqrt{T_\text{obs} \int df \frac{\Omega_\text{signal}^2}{\Omega_\text{noise}^2}}$,
which is :smith_2019:`\ ` eq. 60.
The noise that is fed into it therefore has to be defined the way :smith_2019:`\ ` defines it.

Differences between the .txt files and the PTtools noise
--------------------------------------------------------
The old curves contain the instrument noise only,
and therefore the compact binary noises have to be disabled when comparing with PTtools.
Even then, the old curves are smaller than the PTtools instrument noise
by the constant factor :py:const:`SENSITIVITY_FILE_FACTOR` $\approx 5.98$, which consists of

- A factor of $2$ from the $S \rightarrow \Omega$ conversion,
  since :py:func:`ptplot.science.sensitivity.sciencerequirements.OmSens`
  uses the $2 \pi^2$ of :caprini_2020:`\ ` eq. 34.
- A factor of $2 \sqrt{2}$ from the strain sensitivity itself.
  :py:func:`ptplot.science.sensitivity.sciencerequirements.Sh` applies a factor of $\frac{1}{2}$
  to the :lisa_sci_req:`\ ` eq. 3 single-channel sensitivity $\frac{20}{3} (\ldots)$.
  Of this, $\sqrt{2}$ is from using $\frac{1}{2}$ instead of $\frac{1}{\sqrt{2}}$
  as the gain of the two channels,
  and $2$ is from applying that gain to the $\frac{20}{3}$ sensitivity of the
  equivalent Michelson channel instead of the $\frac{40}{3}$ sensitivity of the A and E channels.
- A factor of $\left( \frac{H_{100,\text{files}}}{H_{100}} \right)^2 \approx 1.058$
  from the value of the Hubble constant.
  The files were generated with $1 \ \text{Mpc} = 3.0 \cdot 10^{19} \ \text{km}$,
  whereas PTtools uses the CODATA value.

Together the first two give $4 \sqrt{2} \approx 5.657$,
which is the factor between the two conventions when the same $H_0$ is used.

The factor is not exactly constant across the band, for two reasons:

- The old curves use $f_2 = 25 \ \text{mHz}$, whereas :lisa_sci_req:`\ ` eq. 3 defines
  $f_2 = \frac{4}{3} f_t = 25.45 \ \text{mHz}$ (:py:data:`pttools.omgw0.noise.F2_LISA`).
  This makes the old curves up to 3.6 % too small above $f_2$.
- :py:func:`pttools.omgw0.noise.omega_noise_h2` uses the exact
  :py:func:`pttools.omgw0.noise.S_AE` (:smith_2019:`\ ` eq. 57)
  rather than the low-frequency approximation of the old curves,
  so the two also differ by the $\cos \frac{f}{f_t}$ terms above roughly 1 mHz.

The tests below therefore compare with the exact noise only below
:py:const:`F_MAX_EXACT`, and with the approximate noise over the whole band.

:smith_2019:`\ ` sec. VI discusses how the SNR differs by factors of this size
between long-lived and short-lived sources,
but the factor found here is fully explained by the conventions listed above,
and is therefore not a long-lived vs. short-lived source difference.
A phase transition background is long-lived in this sense,
so :smith_2019:`\ ` eq. 60 is the correct SNR formula for it, with no extra factors.

The old ``Sens_L6A2M5N2P2D28`` curves are for a different LISA configuration
(C1 of :caprini_2016:`\ `) and are therefore not compared here.
"""

import contextlib
import io
import math
import os.path

from django.test import TestCase
import numpy as np
from pttools.omgw0.const import H0_100_HZ
from pttools.omgw0.noise import S_AE_approx, omega_h2, omega_noise_h2
import pytest

from ptplot.science.const import YEAR_IN_SECONDS
from ptplot.science.noise import DEFAULT_OBS_YEARS, Noise, noise_curve
from ptplot.science.sensitivity import sciencerequirements as req
import ptplot.science.type_hints as th

SENSITIVITY_ROOT: str = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "science", "sensitivity"
)
#: Names of the old sensitivity curves that were generated with
#: :py:mod:`ptplot.science.sensitivity.sciencerequirements`
SENSITIVITY_FILES: tuple[str, ...] = ("ScienceRequirements", "ScienceRequirementsLite")
#: The curve that :py:func:`ptplot.science.sensitivity.sciencerequirements.main` generates
MAIN_SENSITIVITY_FILE: str = "ScienceRequirements"

#: Factor between the old and the PTtools instrument noise, when the same $H_0$ is used
CONVENTION_FACTOR: float = 4 / math.sqrt(2) * 2
#: Factor between the saved sensitivity files and the PTtools instrument noise
SENSITIVITY_FILE_FACTOR: float = CONVENTION_FACTOR * (req.H100_OLD / H0_100_HZ) ** 2

#: Relative tolerance of the comparison with :py:func:`OmSens`,
#: set by the six significant digits with which the files were written
RTOL_FILE_PRECISION: float = 1e-4

#: Below this frequency the exact and the approximate LISA responses agree
F_MAX_EXACT: float = 1e-3
#: Relative tolerance of the comparison in the low-frequency band
RTOL_LOW_F: float = 2e-3
#: Relative tolerance of the comparison over the full band.
#: The residual comes from the transfer frequency:
#: the old curves use $f_2 = 25 \ \text{mHz}$, whereas PTtools uses $\frac{4}{3} f_t = 25.45 \ \text{mHz}$.
RTOL_FULL_BAND: float = 4e-2


def load_sensitivity(name: str) -> tuple[th.FloatArr1D, th.FloatArr1D]:
    r"""Load the frequencies $f$ and the sensitivities $\Omega_\text{sens} h^2$ of an old curve."""
    # The output must be C-contiguous, so that it can be passed to the Numba-compiled PTtools functions.
    f, sensitivity = np.ascontiguousarray(
        np.loadtxt(os.path.join(SENSITIVITY_ROOT, f"{name}.txt"), usecols=(0, 2), unpack=True)
    )
    return f, sensitivity


class NoiseTest(TestCase):
    """Tests for the noise curve object."""

    @staticmethod
    def test_default():
        noise = noise_curve()
        assert noise.obs_years == DEFAULT_OBS_YEARS
        assert noise.eb
        assert noise.gb
        assert noise.f.size == noise.noise.size
        assert np.all(noise.noise > 0)

    @staticmethod
    def test_cached():
        """The same noise curve should be reused instead of being generated again."""
        assert noise_curve(obs_years=4, eb=False, gb=False) is noise_curve(obs_years=4, eb=False, gb=False)

    @staticmethod
    def test_components():
        """Disabling a noise source should lower the total noise."""
        full = Noise()
        ins_only = Noise(eb=False, gb=False)
        assert np.all(ins_only.noise <= full.noise)
        assert np.any(ins_only.noise < full.noise)

    @staticmethod
    def test_obs_time():
        assert Noise(obs_years=3).obs_time == 3 * YEAR_IN_SECONDS

    @staticmethod
    def test_invalid():
        with pytest.raises(ValueError, match="Invalid obs_years"):
            Noise(obs_years=0)
        with pytest.raises(ValueError, match="Invalid frequency range"):
            Noise(f_min=1, f_max=1e-6)


class SensitivityFileTest(TestCase):
    """Compare the old precomputed sensitivity curves with the PTtools noise."""

    @staticmethod
    def test_main_reproduces_the_file():
        """The module should still generate the exact file that was saved with it.

        This pins down the outdated $H_0$ of
        :py:func:`ptplot.science.sensitivity.sciencerequirements.OmSens`.
        """
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            req.main()
        with open(os.path.join(SENSITIVITY_ROOT, f"{MAIN_SENSITIVITY_FILE}.txt")) as file:
            saved = file.read()
        assert out.getvalue() == saved, f"main() no longer reproduces {MAIN_SENSITIVITY_FILE}.txt."

    @staticmethod
    def test_files_match_the_formula():
        r"""The saved files should equal :py:func:`OmSens`.

        The residual is the six significant digits with which the files were written.
        """
        for name in SENSITIVITY_FILES:
            f, sensitivity = load_sensitivity(name)
            np.testing.assert_allclose(
                sensitivity, np.asarray(req.OmSens(f)), rtol=RTOL_FILE_PRECISION,
                err_msg=f"The saved {name}.txt does not match OmSens()."
            )

    @staticmethod
    def test_files_h0():
        r"""The $H_0$ of the old curves should be the outdated one, not the PTtools one."""
        assert req.H100_OLD > H0_100_HZ
        np.testing.assert_allclose(req.H100_OLD / H0_100_HZ, 1.0286, rtol=1e-4)

    @staticmethod
    def test_low_frequency():
        r"""At low frequencies the PTtools instrument noise is a constant factor above the old curves."""
        for name in SENSITIVITY_FILES:
            f, sensitivity = load_sensitivity(name)
            low_f = f <= F_MAX_EXACT
            np.testing.assert_allclose(
                omega_noise_h2(f[low_f], eb=False, gb=False),
                SENSITIVITY_FILE_FACTOR * sensitivity[low_f],
                rtol=RTOL_LOW_F,
                err_msg=f"The low-frequency part of {name}.txt does not match the PTtools instrument noise."
            )

    @staticmethod
    def test_full_band():
        r"""Over the full band the approximate PTtools noise matches the old curves to a few per cent."""
        for name in SENSITIVITY_FILES:
            f, sensitivity = load_sensitivity(name)
            np.testing.assert_allclose(
                omega_h2(f=f, S=S_AE_approx(f)),
                SENSITIVITY_FILE_FACTOR * sensitivity,
                rtol=RTOL_FULL_BAND,
                err_msg=f"{name}.txt does not match the approximate PTtools instrument noise."
            )

    @staticmethod
    def test_factor():
        """The factor between the old and the new curves should be explained by the conventions."""
        np.testing.assert_allclose(CONVENTION_FACTOR, 4 * math.sqrt(2))
        np.testing.assert_allclose(SENSITIVITY_FILE_FACTOR, 5.9846, rtol=1e-4)
