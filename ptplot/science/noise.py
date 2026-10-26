r"""LISA noise curves.

The noise curves are generated at runtime with PTtools and cached,
so that the same curve can be reused for several SNR points.

The old precomputed sensitivity curves are kept in :py:mod:`ptplot.science.sensitivity` for reference.
Please see :py:mod:`ptplot.tests.test_noise` for a comparison of the old and the new curves.
"""

import functools
import math
import typing as tp

import numpy as np
from pttools.omgw0 import omega_noise_h2

from ptplot.science.const import (
    DEFAULT_F_MAX,
    DEFAULT_F_MIN,
    DEFAULT_F_RANGE,
    DEFAULT_F_SIZE,
    DEFAULT_OBS_YEARS,
    MIN_F_SIZE,
    YEAR_IN_SECONDS,
)
import ptplot.science.type_hints as th

#: Whether the extragalactic compact binary noise $\Omega_\text{eb}$ is included by default
DEFAULT_NOISE_EB: bool = False
#: Whether the galactic compact binary noise $\Omega_\text{gb}$ is included by default
DEFAULT_NOISE_GB: bool = False
# Number of :py:class:`Noise` objects that are kept in cache
NOISE_CACHE_SIZE: tp.Final[int] = 16


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
            f_min: float = DEFAULT_F_MIN,
            f_max: float = DEFAULT_F_MAX,
            size: int = DEFAULT_F_SIZE):
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

        #: Frequencies $f$ (Hz) corresponding to the noise values
        self.f: th.FloatArr1D
        if f_min == DEFAULT_F_MIN and f_max == DEFAULT_F_MAX and size == DEFAULT_F_SIZE:
            self.f = DEFAULT_F_RANGE
        else:
            if not 0 < f_min < f_max:
                raise ValueError(f"Invalid frequency range: f_min={f_min}, f_max={f_max}")
            if size < MIN_F_SIZE:
                raise ValueError(f"Invalid size={size}")
            self.f = np.logspace(math.log10(f_min), math.log10(f_max), size)

        #: Mission duration $T_\text{obs}$ in years
        self.obs_years: float = obs_years
        #: Whether the extragalactic compact binary noise $\Omega_\text{eb}$ is included
        self.eb: bool = eb
        #: Whether the galactic compact binary noise $\Omega_\text{gb}$ is included
        self.gb: bool = gb
        #: Noise $\Omega_\text{noise} h^2$
        self.noise: th.FloatArr1D = omega_noise_h2(f=self.f, eb=self.eb, gb=self.gb)

    def __str__(self) -> str:
        """Describe the noise curve, including its mission duration and noise sources."""
        sources = ["instrument"]
        if self.eb:
            sources.append("extragalactic compact binaries")
        if self.gb:
            sources.append("galactic compact binaries")
        return f"LISA, {self.obs_years:g} years, noise from {', '.join(sources)}"

    @property
    def f_min(self) -> np.float64:
        r"""Minimum frequency $f_\text{min}$ (Hz)."""
        return self.f[0]

    @property
    def f_max(self) -> np.float64:
        r"""Maximum frequency $f_\text{max}$ (Hz)."""
        return self.f[-1]

    @property
    def file_name(self) -> str:
        """Name that identifies this noise curve in file names."""
        return f"LISA_{self.obs_years:g}yr" + ("_eb" if self.eb else "") + ("_gb" if self.gb else "")

    @property
    def obs_time(self) -> float:
        r"""Mission duration $T_\text{obs}$ in seconds."""
        return self.obs_years * YEAR_IN_SECONDS

    def noise_at(self, f: th.FloatArr1D) -> th.FloatArr1D:
        r"""Noise $\Omega_\text{noise} h^2$ with the noise sources of this curve at the given frequencies.

        :param f: Frequencies $f$ (Hz)
        :return: $\Omega_\text{noise} h^2$ at ``f``
        """
        return omega_noise_h2(f=f, eb=self.eb, gb=self.gb)


@functools.lru_cache(maxsize=NOISE_CACHE_SIZE)
def _noise_curve(obs_years: float, eb: bool, gb: bool, f_min: float, f_max: float, size: int) -> Noise:
    """Cache of the noise curves, keyed by positional arguments only."""
    return Noise(obs_years=obs_years, eb=eb, gb=gb, f_min=f_min, f_max=f_max, size=size)


def noise_curve(
        obs_years: float = DEFAULT_OBS_YEARS,
        eb: bool = DEFAULT_NOISE_EB,
        gb: bool = DEFAULT_NOISE_GB,
        f_min: float = DEFAULT_F_MIN,
        f_max: float = DEFAULT_F_MAX,
        size: int = DEFAULT_F_SIZE) -> Noise:
    """Get a cached noise curve, or generate it if it has not been generated yet.

    The arguments are the same as for :py:class:`Noise`.
    They are passed on as positional arguments, so that calls with and without
    the default values are found in the same cache entry.
    """
    return _noise_curve(obs_years, eb, gb, f_min, f_max, size)


def resolve_noise(noise: Noise | None) -> Noise:
    """Get the default noise curve, if a noise curve was not given."""
    return noise_curve() if noise is None else noise
