r"""LISA noise curves.

The noise curves are generated at runtime with PTtools and cached,
so that the same curve can be reused for several SNR points.

The old precomputed sensitivity curves are kept in :py:mod:`ptplot.science.sensitivity` for reference.
Please see :py:mod:`ptplot.tests.test_noise` for a comparison of the old and the new curves.
"""

import functools
import math

import numpy as np
from pttools.omgw0 import omega_noise_h2

from ptplot.science.const import DEFAULT_SNR_F_MAX, DEFAULT_SNR_F_MIN, YEAR_IN_SECONDS
import ptplot.science.type_hints as th

#: Default LISA mission duration $T_\text{obs}$ in years
DEFAULT_OBS_YEARS: float = 3.
#: Whether the extragalactic compact binary noise $\Omega_\text{eb}$ is included by default
DEFAULT_NOISE_EB: bool = True
#: Whether the galactic compact binary noise $\Omega_\text{gb}$ is included by default
DEFAULT_NOISE_GB: bool = True
#: Default number of frequency points of a noise curve
DEFAULT_NOISE_SIZE: int = 2000
#: Minimum number of frequency points of a noise curve
MIN_NOISE_SIZE: int = 2


class Noise:
    r"""LISA noise curve $\Omega_\text{noise} h^2$ and the mission duration it is observed for.

    The instrument noise $\Omega_\text{ins}$ is always included.
    The compact binary noises are optional, as they can be subtracted from the data
    by resolving and removing the individual binaries.

    Use :py:func:`noise_curve` to get a cached instance instead of creating a new one.
    """

    def __init__(
            self,
            obs_years: float = DEFAULT_OBS_YEARS,
            eb: bool = DEFAULT_NOISE_EB,
            gb: bool = DEFAULT_NOISE_GB,
            f_min: float = DEFAULT_SNR_F_MIN,
            f_max: float = DEFAULT_SNR_F_MAX,
            size: int = DEFAULT_NOISE_SIZE):
        r"""
        Create a noise curve.

        :param obs_years: Mission duration $T_\text{obs}$ in years
        :param eb: Whether to include the extragalactic compact binary noise $\Omega_\text{eb}$
        :param gb: Whether to include the galactic compact binary noise $\Omega_\text{gb}$
        :param f_min: Minimum frequency $f_\text{min}$ (Hz)
        :param f_max: Maximum frequency $f_\text{max}$ (Hz)
        :param size: Number of frequency points
        """
        if obs_years is None or not np.isfinite(obs_years) or obs_years <= 0:
            raise ValueError(f"Invalid obs_years={obs_years}")
        if not 0 < f_min < f_max:
            raise ValueError(f"Invalid frequency range: f_min={f_min}, f_max={f_max}")
        if size < MIN_NOISE_SIZE:
            raise ValueError(f"Invalid size={size}")

        #: Mission duration $T_\text{obs}$ in years
        self.obs_years: float = obs_years
        #: Whether the extragalactic compact binary noise $\Omega_\text{eb}$ is included
        self.eb: bool = eb
        #: Whether the galactic compact binary noise $\Omega_\text{gb}$ is included
        self.gb: bool = gb
        #: Frequencies $f$ (Hz) corresponding to the noise values
        self.f: th.FloatArr1D = np.logspace(math.log10(f_min), math.log10(f_max), size)
        #: Noise $\Omega_\text{noise} h^2$
        self.noise: th.FloatArr1D = omega_noise_h2(f=self.f, eb=self.eb, gb=self.gb)

    def __str__(self) -> str:
        sources = ["instrument"]
        if self.eb:
            sources.append("extragalactic compact binaries")
        if self.gb:
            sources.append("galactic compact binaries")
        return f"LISA, {self.obs_years:g} years, noise from {', '.join(sources)}"

    @property
    def f_min(self) -> float:
        r"""Minimum frequency $f_\text{min}$ (Hz)."""
        return self.f[0].item()

    @property
    def f_max(self) -> float:
        r"""Maximum frequency $f_\text{max}$ (Hz)."""
        return self.f[-1].item()

    @property
    def file_name(self) -> str:
        """Name that identifies this noise curve in file names."""
        return f"LISA_{self.obs_years:g}yr" + ("_eb" if self.eb else "") + ("_gb" if self.gb else "")

    @property
    def obs_time(self) -> float:
        r"""Mission duration $T_\text{obs}$ in seconds."""
        return self.obs_years * YEAR_IN_SECONDS


@functools.lru_cache(maxsize=16)
def _noise_curve(obs_years: float, eb: bool, gb: bool, f_min: float, f_max: float, size: int) -> Noise:
    """Cache of the noise curves, keyed by positional arguments only."""
    return Noise(obs_years=obs_years, eb=eb, gb=gb, f_min=f_min, f_max=f_max, size=size)


def noise_curve(
        obs_years: float = DEFAULT_OBS_YEARS,
        eb: bool = DEFAULT_NOISE_EB,
        gb: bool = DEFAULT_NOISE_GB,
        f_min: float = DEFAULT_SNR_F_MIN,
        f_max: float = DEFAULT_SNR_F_MAX,
        size: int = DEFAULT_NOISE_SIZE) -> Noise:
    """Get a cached noise curve, or generate it if it has not been generated yet.

    The arguments are the same as for :py:class:`Noise`.
    They are passed on as positional arguments, so that calls with and without
    the default values are found in the same cache entry.
    """
    return _noise_curve(obs_years, eb, gb, f_min, f_max, size)


def resolve_noise(noise: Noise | None) -> Noise:
    """Get the default noise curve, if a noise curve was not given."""
    return noise_curve() if noise is None else noise
