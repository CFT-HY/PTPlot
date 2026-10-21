"""Constants and helpers of the Sound Shell Model (SSM) tests."""

import functools
import typing as tp

import numpy as np
from pttools.bubble import Bubble

from ptplot.science.noise import noise_curve
from ptplot.science.spectrum.ssm import BAG, PowerSpectrumSSM
from ptplot.tests.old_ptplot import f_star0_factor

ALPHA: float = 0.1
BETA_TILDE: float = 100.
T_STAR: float = 100.
G_STAR: float = 100.
#: Subsonic deflagration and detonation
V_WALLS: tuple[float, ...] = (0.3, 0.9)
#: Reference values of $r_*$, SNR and $\mathcal{H}_* \eta_\text{sh}$ for each wall velocity,
#: computed with PTPlot before the fix of the ``bubble`` argument of :class:`PowerSpectrumSSM` in October 2026,
#: and therefore with the old $f_{\ast,0}$ of PTtools, see :py:data:`F_STAR0_FACTOR`,
#: and with the compact binary noises, which were included by default at the time.
#: The SNR values have since been updated for the following changes in PTtools:
#:
#: - 3d5798f: the point at the wall of detonations is in the broken phase (v_wall = 0.9: 0.11508 -> 0.11346)
#: - 137b476: the suppression datasets are recomputed with SSMSpectrum
#:   (v_wall = 0.3: 0.05727 -> 0.06623, v_wall = 0.9: 0.11346 -> 0.10879)
#: - 0c54ca3: the default suppression dataset is WITH_HYBRIDS_EXT instead of NO_HYBRIDS_EXT
#:   (v_wall = 0.9: 0.10879 -> 0.11086)
#: - 1ba25c7: the thin shells of hybrids are preserved in the sine transforms
#:   (v_wall = 0.3: 0.06623 -> 0.06630, v_wall = 0.9: 0.11086 -> 0.11071)
#: - 589a166: the sine transforms of the fluid profiles are exact for large z
#:   (v_wall = 0.3: 0.06630 -> 0.06625, v_wall = 0.9: 0.11071 -> 0.11079)
#: - d61dd9b: the suppression datasets are recomputed with the exact sine transforms
#:   (v_wall = 0.3: 0.06625 -> 0.06630, v_wall = 0.9: 0.11079 -> 0.11089)
REFERENCE: dict[float, tuple[float, float, float]] = {
    0.3: (0.018124666532740186, 0.06630315099614825, 0.19839872059716177),
    0.9: (0.026362653976107417, 0.1108899128817558, 0.2568295035856295),
}

#: $\tilde{\beta}$ values of the columns for testing the precomputed spectra, covering 4 orders of magnitude
BETA_TILDES: tuple[float, ...] = (10., 100., 1000., 1e5)
#: Relative tolerance for the SNR computed on the points of a precomputed spectrum.
#: The SNR differs from that of a separately computed spectrum due to the different points.
SNR_RTOL_PRECOMPUTED: float = 1e-3
#: Relative tolerance for the power spectrum interpolated from a precomputed spectrum
#: at the frequencies where it is above :py:data:`PS_REL_MIN_PRECOMPUTED` times its peak,
#: see :py:meth:`ptplot.tests.spectrum.ssm.test_reference.SSMReferenceTest.test_precomputed`.
PS_RTOL_PRECOMPUTED: float = 2e-2
PS_REL_MIN_PRECOMPUTED: float = 1e-2

#: Ratio of the old and the new $f_{\ast,0}$ of PTtools, see :py:func:`ptplot.tests.old_ptplot.f_star0_factor`
F_STAR0_FACTOR: float = f_star0_factor(T_STAR, G_STAR)


def spectrum(
        v_wall: float,
        alpha: float | None = ALPHA,
        beta_tilde: float | None = BETA_TILDE,
        T_star: float = T_STAR,
        g_star: float = G_STAR,
        **kwargs: tp.Any) -> PowerSpectrumSSM:
    """Create an SSM power spectrum with the test parameters, which can be overridden."""
    return PowerSpectrumSSM.cached(
        v_wall=v_wall, alpha=alpha, beta_tilde=beta_tilde, T_star=T_star, g_star=g_star, **kwargs
    )


@functools.cache
def reference(v_wall: float, beta_tilde: float = BETA_TILDE) -> tuple[PowerSpectrumSSM, np.ndarray, float]:
    """SSM power spectrum with the cached fluid shell, computed for the default noise curve.

    The power spectrum and the SNR are cached, as several tests compare against them,
    and computing them is slow.

    :return: The spectrum, its power spectrum at the frequencies of the default noise curve, and its SNR
    """
    noise = noise_curve()
    ssm = spectrum(v_wall, bubble=Bubble.cached(model=BAG, v_wall=v_wall, alpha_n=ALPHA), beta_tilde=beta_tilde)
    ps, snr = ssm.power_spectrum(noise.f, noise=noise)
    return ssm, ps, snr
