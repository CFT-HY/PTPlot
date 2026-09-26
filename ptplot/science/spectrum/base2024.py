"""Base class for the power law templates of Caprini et al. (2024)."""

import abc
import typing as tp

import numpy as np
from scipy.optimize import brentq

from ptplot.science.noise import Noise, resolve_noise
from ptplot.science.spectrum.base import PowerSpectrum
import ptplot.science.type_hints as th
from ptplot.science.type_hints import FloatOrArr


class PowerSpectrum2024(PowerSpectrum, abc.ABC):
    r"""Base class for the broken power law templates of :caprini_2024:`\ `.

    Equation and page numbers refer to arXiv:2403.03723v2.
    The spectrum is a power law $f^{n_1}$, which is broken at the frequencies $f_i$ to $f^{n_{i+1}}$
    with the smoothness parameters $a_i$.
    It is normalized to its value at a reference frequency $f_{\text{ref}}$,
    which is $f_b$ for the broken power law (BPL) and $f_2$ for the double broken power law (DBPL).
    """

    #: $n_1, n_2, \ldots$, spectral slopes, :caprini_2024:`\ ` table 1
    SLOPES: tuple[float, ...]
    #: $a_1, a_2, \ldots$, smoothness parameters of the breaks, :caprini_2024:`\ ` table 1
    SMOOTHNESS: tuple[float, ...]

    @abc.abstractmethod
    def f_breaks(self) -> tuple[float, ...]:
        r"""$f_1, f_2, \ldots$, break frequencies."""

    @abc.abstractmethod
    def f_ref(self) -> float:
        r"""$f_{\text{ref}}$, reference frequency at which the spectrum is normalized to its amplitude."""

    @abc.abstractmethod
    def omega_ref_h2(self) -> float:
        r"""$h^2 \Omega_{\text{gw}}(f_{\text{ref}})$, amplitude of the spectrum at the reference frequency."""

    def _breaks(self) -> tp.Iterator[tuple[float, float, float, float]]:
        """Slopes $n_i$ and $n_{i+1}$, smoothness $a_i$ and frequency $f_i$ of each break."""
        return zip(self.SLOPES[:-1], self.SLOPES[1:], self.SMOOTHNESS, self.f_breaks(), strict=True)

    def d_ln_S_d_ln_f(self, ln_f: float) -> float:
        r"""Logarithmic slope of the spectrum.

        $$\frac{d \ln S}{d \ln f} = n_1 + \sum_i (n_{i+1} - n_i) \frac{y_i}{1 + y_i},
        \quad y_i = \left( \frac{f}{f_i} \right)^{a_i}$$

        :param ln_f: $\ln f$, logarithm of the frequency
        :return: $\frac{d \ln S}{d \ln f}$
        """
        f = np.exp(ln_f)
        slope = self.SLOPES[0]
        for n_low, n_high, a, f_break in self._breaks():
            y = (f / f_break)**a
            slope += (n_high - n_low) * y / (1 + y)
        return slope

    def f_peak(self) -> float:
        r"""$f_p$, peak frequency of the spectrum.

        See :py:meth:`f_peak_numerical`.
        """
        return self.f_peak_numerical()

    def f_peak_numerical(self) -> float:
        r"""$f_p$, peak frequency of the spectrum, found numerically.

        This is the root of $\frac{d \ln S}{d \ln f}$,
        which decreases monotonically from $n_1 > 0$ to the last slope, which is $< 0$.
        """
        f_breaks = self.f_breaks()
        return float(np.exp(brentq(self.d_ln_S_d_ln_f, np.log(f_breaks[0]) - 10, np.log(f_breaks[-1]) + 10)))

    def shape[T: FloatOrArr](self, f: T) -> T:
        r"""Spectral shape normalized to 1 at the reference frequency $f_{\text{ref}}$.

        $$\frac{S(f)}{S(f_{\text{ref}})}, \quad
        S(f) \propto \left( \frac{f}{f_1} \right)^{n_1}
        \prod_i \left[ 1 + \left( \frac{f}{f_i} \right)^{a_i} \right]^\frac{n_{i+1} - n_i}{a_i}$$
        :caprini_2024:`\ ` eq. 2.4 and 2.8

        :param f: $f$, frequency
        :return: Normalized spectral shape
        """
        return tp.cast(T, self._shape_unnormalized(f) / self._shape_unnormalized(self.f_ref()))

    def _shape_unnormalized(self, f: FloatOrArr) -> FloatOrArr:
        s = (f / self.f_breaks()[0])**self.SLOPES[0]
        for n_low, n_high, a, f_break in self._breaks():
            s = s * (1 + (f / f_break)**a)**((n_high - n_low) / a)
        return s

    def power_spectrum(
            self,
            f: th.FloatArr1D,
            noise: Noise | None = None,
            log_errors: bool = False) -> tuple[th.FloatArr1D, float]:  # noqa: ARG002
        r"""GW power spectrum using a power law template of :caprini_2024:`\ `.

        $$h^2 \Omega_{\text{gw}}(f) = h^2 \Omega_{\text{gw}}(f_{\text{ref}}) \frac{S(f)}{S(f_{\text{ref}})}$$
        :caprini_2024:`\ ` eq. 2.4 and 2.8
        """
        power_spectrum = tp.cast("th.FloatArr1D", self.omega_ref_h2() * self.shape(f))
        return power_spectrum, self.snr(f=f, power_spectrum=power_spectrum, noise=resolve_noise(noise))
