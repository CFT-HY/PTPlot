r"""Double broken power law (DBPL) power spectrum of Gowling & Hindmarsh (2021).

The spectral parameters $\hat{\Omega}_p$, $z_b$, $z_p$ and $b$ of the DBPL are functions of
$v_{\text{wall}}$ and $\alpha_n$, which are found by fitting the DBPL to the Sound Shell Model (SSM) spectra
$\hat{\mathcal{P}}_\text{gw}(z)$ of :gowling_2021:`\ ` eq. 2.14 in :py:data:`SSM_DATA_PATH`.
These spectra were computed by Chloe Gowling with an early version of PTtools for :gowling_2021:`\ ` fig. 3.
The fit follows the script ``parameter_dependence/fit_power_gw_scaled_to_obs_ssm.py``
of the ``fisher_analysis`` repository of :gowling_2021:`\ `.
"""

import dataclasses
import functools
import logging
import os
from pathlib import Path
import tempfile
import typing as tp
import warnings

import numpy as np
from numpy.lib.npyio import NpzFile
from pttools.omgw0.const import H
from pttools.speedup import njit
from pttools.ssm import J_old
from pttools.ssm.suppression import GH21, Suppression, SuppressionMethod
from pttools.utils.system import pttools_version
from scipy.interpolate import RegularGridInterpolator
from scipy.optimize import curve_fit

from ptplot.science.const import CS0, DEFAULT_ADIABATIC_INDEX, DEFAULT_G_STAR, DEFAULT_T_STAR
from ptplot.science.noise import Noise
from ptplot.science.spectrum.coswg20 import DEFAULT_ZP, CosWG20
from ptplot.science.spectrum.engine import Engine
import ptplot.science.type_hints as th
from ptplot.science.type_hints import FloatOrArr
from ptplot.science.utils import ptplot_version

__all__ = [
    "SSM_DATA_PATH",
    "SSM_FIT_PATH",
    "GH21dbpl",
    "GH21dbplFit",
    "GH21dbplParams",
    "M",
    "cached_dbpl_fit",
    "data_key",
    "data_points",
    "delta2",
    "fit_dbpl_to_ssm",
    "m",
]

logger: logging.Logger = logging.getLogger(__name__)

#: SSM spectra $\hat{\mathcal{P}}_\text{gw}(z)$ of :gowling_2021:`\ ` on a grid of
#: 51 linearly spaced $v_{\text{wall}} \in [0.4, 0.9]$, 50 logarithmically spaced $\alpha_n \in [0.01, 0.5]$
#: and 100 logarithmically spaced $z \in [1, 1000]$.
#: The spectra are stored with the keys ``vw{v_wall}al{alpha_n}``, where the dots are replaced with underscores.
SSM_DATA_PATH: Path = Path(__file__).resolve().parent / "pgw16_11_20_params50_51_log_alpha_vw.npz"
#: Cache file of :py:func:`cached_dbpl_fit`, which is created on the first use,
#: as fitting the whole grid takes some time.
#: It is recreated when the version of PTPlot or PTtools changes, and removed by ``install_requirements.sh``.
SSM_FIT_PATH: Path = SSM_DATA_PATH.with_name("gh21dbpl_fit.npz")


@dataclasses.dataclass(frozen=True, slots=True)
class GH21dbplFit:
    r"""Best-fit DBPL parameters on a grid of $v_{\text{wall}}$ and $\alpha_n$.

    The 2D arrays are indexed as ``[alpha_n, v_wall]``.
    """

    #: $v_{\text{wall}}$, wall speeds of the grid
    v_walls: th.FloatArr1D
    #: $\alpha_n$, transition strengths of the grid
    alpha_ns: th.FloatArr1D
    #: $\hat{\Omega}_p$, peak value of $\hat{\mathcal{P}}_\text{gw}$
    omega_p_hat: th.FloatArr2D
    #: $z_b$, $z$ of the lower break
    zb: th.FloatArr2D
    #: $z_p$, $z$ of the peak
    zp: th.FloatArr2D
    #: $b$, spectral slope between the breaks
    b: th.FloatArr2D
    #: $\delta_\mathcal{P}^2$, mean squared relative deviation of the fit, :gowling_2021:`\ ` eq. B.1
    delta2: th.FloatArr2D

    @property
    def rb(self) -> th.FloatArr2D:
        r"""$r_b = z_b / z_p$, ratio of the break frequencies."""
        return self.zb / self.zp

    def in_range(self, v_wall: float, alpha_n: float) -> bool:
        r"""Whether the point is within the grid."""
        return bool(
            self.v_walls[0] <= v_wall <= self.v_walls[-1] and self.alpha_ns[0] <= alpha_n <= self.alpha_ns[-1]
        )

    def interpolate(self, v_wall: float, alpha_n: float) -> tuple[float, float, float, float]:
        r"""Interpolate the DBPL parameters linearly on the $(\log \alpha_n, v_{\text{wall}})$ plane.

        $\hat{\Omega}_p$, $z_b$ and $z_p$ are interpolated logarithmically, and $b$ linearly.
        Points outside the grid are moved to its closest edge, with a warning.

        :param v_wall: $v_{\text{wall}}$, wall speed
        :param alpha_n: $\alpha_n$, transition strength
        :return: $\hat{\Omega}_p$, $z_b$, $z_p$, $b$
        """
        if not self.in_range(v_wall, alpha_n):
            warnings.warn(
                "The given GH21dbpl parameters are outside the grid of the SSM fit, "
                f"v_wall=[{self.v_walls[0]}, {self.v_walls[-1]}], "
                f"alpha_n=[{self.alpha_ns[0]}, {self.alpha_ns[-1]}]. "
                "Using the values at the closest edge of the grid.",
                stacklevel=2
            )
        point = (
            np.log(np.clip(alpha_n, self.alpha_ns[0], self.alpha_ns[-1])),
            np.clip(v_wall, self.v_walls[0], self.v_walls[-1])
        )
        values = np.stack((np.log(self.omega_p_hat), np.log(self.zb), np.log(self.zp), self.b), axis=-1)
        log_omp, log_zb, log_zp, b = RegularGridInterpolator((np.log(self.alpha_ns), self.v_walls), values)(point)
        return float(np.exp(log_omp)), float(np.exp(log_zb)), float(np.exp(log_zp)), float(b)


class GH21dbpl(CosWG20):
    r"""
    Double broken power law (DBPL) power spectrum of Gowling & Hindmarsh (2021).

    $$\Omega_{\text{gw},0}(f) = F_{\text{gw},0} J \hat{\Omega}_p(v_{\text{wall}}, \alpha_n)
    \Sigma(v_{\text{wall}}, \alpha_n) M(s, r_b, b)$$
    :gowling_2021:`\ ` eq. 2.15, 2.18,
    where the spectral parameters $\hat{\Omega}_p$, $z_p$, $r_b = z_b / z_p$ and $b$
    are interpolated from the fit of the DBPL to the SSM spectra (:py:func:`cached_dbpl_fit`),
    and $\Sigma$ is the kinetic energy suppression factor of :py:mod:`pttools.ssm.suppression`.
    By default, $\Sigma$ is that of :gowling_2021:`\ ` app. A, :py:data:`pttools.ssm.suppression.GH21`,
    with its fill value outside the convex hull of the data points
    (:py:attr:`pttools.ssm.suppression.SuppressionMethod.EXT_FILL`), as in the original code of the article.
    The earlier default of this class is
    ``suppression=pttools.ssm.suppression.DEFAULT_SUPPRESSION, suppression_method=SuppressionMethod.EXT_CONSTANT``.
    The SSM fit covers $0.4 \leq v_{\text{wall}} \leq 0.9$ and $0.01 \leq \alpha_n \leq 0.5$.
    Outside this range the parameters at the closest edge of the grid are used.

    With ``legacy=True``, this is the earlier DBPL of PTPlot, based on
    :hakkinen_ptplot:`\ `, :hakkinen_msc:`\ ` and :gw_pt_ssm:`\ `,
    which uses the $\tilde{\Omega}_\text{gw}$ normalization of :py:meth:`power_spectrum_common`
    with fixed $z_p$, $z_b$ and $b$ instead of the SSM fit.
    """

    COLOR = "green"
    ENGINE: tp.ClassVar[Engine] = Engine.GH21dbpl
    TABLE = f"spectra_{ENGINE}"
    NAME: tp.ClassVar[str] = "Gowling & Hindmarsh 2021 DBPL"
    SHORT_NAME: tp.ClassVar[str] = Engine.GH21dbpl.value

    OLD_J = True

    def __init__(
            self,
            # Primary parameters
            v_wall: float | None = None,
            alpha: float | None = None,
            beta_tilde: float | None = None,
            ubarf: float | None = None,
            r_star: float | None = None,
            T_star: float = DEFAULT_T_STAR,
            g_star: float = DEFAULT_G_STAR,
            # Additional parameters
            adiabatic_index: float = DEFAULT_ADIABATIC_INDEX,
            f_star0_factor: float = 1.,
            # Switches
            legacy_nucleation_cs_max: bool = False,
            legacy: bool = False,
            # Model-specific parameters
            zb: float | None = None,
            zp: float | None = None,
            b: float | None = None,
            suppression: Suppression = GH21,
            suppression_method: SuppressionMethod = SuppressionMethod.EXT_FILL,
            data_path: str | os.PathLike[str] = SSM_DATA_PATH,
            fit_path: str | os.PathLike[str] = SSM_FIT_PATH,
        ):
        r"""Create a DBPL power spectrum.

        :param legacy: Use the earlier DBPL of PTPlot instead of the SSM fit of :gowling_2021:`\ `
        :param zb: $z_b$, angular frequency of the lower break in units of the mean bubble separation.
            Defaults to the SSM fit, or to 1 with ``legacy``.
        :param zp: $z_p$, peak angular frequency in units of the mean bubble separation.
            Defaults to the SSM fit, or to :py:data:`ptplot.science.spectrum.coswg20.DEFAULT_ZP` with ``legacy``.
        :param b: $b$, spectral slope between the breaks. Defaults to the SSM fit, or to 1 with ``legacy``.
        :param suppression: Kinetic energy suppression data. Defaults to that of :gowling_2021:`\ `.
            Not used with ``legacy``.
        :param suppression_method: Kinetic energy suppression method. Defaults to the fill value of the dataset
            outside the convex hull of its data points, as in :gowling_2021:`\ `. Not used with ``legacy``.
        :param data_path: Path to the SSM spectra, see :py:func:`cached_dbpl_fit`. Not used with ``legacy``.
        :param fit_path: Path to the cache file of the fit, see :py:func:`cached_dbpl_fit`.
            Not used with ``legacy``.
        """
        #: Whether this is the earlier DBPL of PTPlot instead of the SSM fit of :gowling_2021:`\ `
        self.legacy: bool = legacy
        super().__init__(
            T_star=T_star, g_star=g_star, v_wall=v_wall,
            alpha=alpha, beta_tilde=beta_tilde,
            ubarf=ubarf, r_star=r_star,
            adiabatic_index=adiabatic_index,
            f_star0_factor=f_star0_factor,
            legacy_nucleation_cs_max=legacy_nucleation_cs_max,
            zp=DEFAULT_ZP if zp is None else zp,
        )
        #: $\hat{\Omega}_p$, peak value of the scale-free spectrum $\hat{\mathcal{P}}_\text{gw}$ of the SSM fit.
        #: NaN with ``legacy``.
        self.omega_p_hat: float = np.nan
        #: $\Sigma$, kinetic energy suppression factor. NaN with ``legacy``.
        self.suppression_factor: float = np.nan
        fit_b: float = 1.
        fit_zb: float = 1.
        if not legacy:
            fit = cached_dbpl_fit(data_path=data_path, fit_path=fit_path)
            self.omega_p_hat, fit_zb, fit_zp, fit_b = fit.interpolate(
                v_wall=tp.cast(float, self.v_wall), alpha_n=self.alpha
            )
            if zp is None:
                self.zp = fit_zp
            self.suppression_factor = suppression.suppression(
                v_wall=tp.cast(float, self.v_wall), alpha_n=self.alpha, method=suppression_method
            )
        #: $b$, spectral slope between the breaks
        self.b: float = fit_b if b is None else b
        #: $z_b$, angular frequency of the lower break in units of the mean bubble separation
        self.zb: float = fit_zb if zb is None else zb

        #: Ratio of the two peaks in the spectrum, $r_b = \frac{f_b}{f_p} = \frac{z_b}{z_p}$, :gowling_2021:`\ ` p. 9
        self.rb: float = self.zb / self.zp

    def J(self, old: bool | None = None) -> float:
        r"""Combined lifetime factor $J$.

        $$J = r_* \left(1 - \frac{1}{\sqrt{1 + 2x}} \right), \quad x = \frac{r_*}{\sqrt{K}}$$
        :gowling_2021:`\ ` eq. 2.7, 2.8.
        This differs from :py:func:`pttools.ssm.scaling.J_old` by having $\sqrt{K}$ instead of $\sqrt{K / \Gamma}$
        in $x$. With ``legacy`` or with ``old`` given, this is :py:meth:`PowerSpectrum.J`.
        """
        if self.legacy or old is not None:
            return super().J(old=old)
        return J_old(r_star=self.r_star, K=self.kinetic_energy_fraction, adiabatic_index=1.)

    def m[T: FloatOrArr](self, b: T | None = None) -> T:
        r"""Compute the value $m$ used in the spectral shape function M(s).

        $$m = \frac{9 r_b^4 + b}{r_b^4 + 1}$$
        :gowling_2021:`\ ` eq. 2.17.
        With $b = 1$, this reduces to
        :gw_pt_ssm:`\ ` p. 22.

        :param b: $b$, spectral slope between the breaks. Defaults to :py:attr:`b`.
        """
        return tp.cast(T, m(rb=self.rb, b=self.b if b is None else b))

    def mu(self) -> float:
        r"""Prefactor $\mu(r_b)$ for the peak power of the GW power spectrum, computed exactly.

        This has not been implemented yet. Please use :py:meth:`mu_approx` instead.

        :raises NotImplementedError: Always
        """
        # Todo: implement the full mu integration to get rid of the 10 % error in the approximation.
        raise NotImplementedError

    def mu_approx(self) -> float:
        r"""Prefactor $\mu(r_b)$ for the peak power of the GW power spectrum.

        $$\mu(r_b) = \int_0^\infty \frac{ds}{s} M(s, r_b) \approx 4.78 - 6.27 r_b + 3.34 r_b^2$$
        This approximation is accurate to about 10 % over the relevant range $0 < r_b < 1$.
        :gw_pt_ssm:`\ ` eq. 5.8, 5.9

        This relates the peak power parameter $A_M$ to the total power parameter $\tilde{\Omega}_\text{gw}$.
        It is used only with ``legacy``.
        """
        return 4.78 - 6.27 * self.rb + 3.34 * self.rb**2

    def M(self, s: th.FloatOrArr, b: th.FloatOrArr | None = None) -> th.FloatOrArr:
        r"""Spectral shape of the GW power spectrum, see :py:func:`ptplot.science.spectrum.gh21dbpl.M`.

        :param s: Frequency $s$ relative to the peak frequency
        :param b: $b$, spectral slope between the breaks. Defaults to :py:attr:`b`.
        :return: Spectral shape $M(s, r_b, b)$
        """
        return M(s=s, rb=self.rb, b=self.b if b is None else b)

    def omega_peak_h2(self) -> float:
        r"""$h^2 \Omega_{p,0}$, peak value of the power spectrum today.

        $$\Omega_{p,0} = F_{\text{gw},0} J \hat{\Omega}_p \Sigma$$
        :gowling_2021:`\ ` eq. 2.18.
        With ``legacy``, this is
        $$\Omega_{p,0} = \frac{3 F_{\text{gw},0} \Gamma^2 \bar{U}_f^4 \tilde{\Omega}_\text{gw} J}{\mu(r_b)}$$
        """
        if self.legacy:
            return self.power_spectrum_common() / self.mu_approx() * self.J()
        return tp.cast(float, self.F_gw0_h2()) * self.J() * self.omega_p_hat * self.suppression_factor

    def power_spectrum(
            self,
            f: th.FloatArr1D,
            noise: Noise | None = None,
            log_errors: bool = False) -> tuple[th.FloatArr1D, float]:  # noqa: ARG002
        r"""Calculate power spectrum from sound waves for a given frequency f using the double broken power-law ansatz.

        $$\Omega_\text{gw}^\text{fit} = F_{\text{gw},0} \Omega_p M(s, r_b, b)$$
        :gowling_2021:`\ ` eq. 2.15, with $\Omega_p$ of :py:meth:`omega_peak_h2`.

        $F_{\text{gw},0}$ depends on the value of $h$,
        which is why the result is multiplied by $h^2$ to get a quantity that is independent of $h$.
        """
        power_spectrum = tp.cast(th.FloatArr1D, self.omega_peak_h2() * self.M(s=self.s(f)))
        return self.snr_and_store(f, power_spectrum, noise)

    def validate_v_wall(self, v_wall: float | None, cs: float = CS0) -> float | None:
        r"""Validate $v_{\text{wall}}$, which is required for the SSM fit."""
        if not self.legacy and (v_wall is None or np.isnan(v_wall)):
            raise ValueError(f"{self.ENGINE.name} requires v_wall to be set unless legacy=True. Got v_wall={v_wall}.")
        return super().validate_v_wall(v_wall=v_wall, cs=cs)


@dataclasses.dataclass(frozen=True, slots=True)
class GH21dbplParams:
    r"""Spectral parameters of :py:class:`GH21dbpl` on a grid of $v_{\text{wall}}$ and $\alpha_n$.

    These are the parameters of :gowling_2021:`\ ` eq. 2.18 and fig. 3.
    The 2D arrays are indexed as ``[alpha_n, v_wall]``.
    """

    #: $v_{\text{wall}}$, wall speeds of the grid
    v_walls: th.FloatArr1D
    #: $\alpha_n$, transition strengths of the grid
    alpha_ns: th.FloatArr1D
    #: $r_*$, Hubble-scaled mean bubble spacing
    r_star: float
    #: $T_*$, transition temperature
    T_star: float
    #: $g_*$, degrees of freedom
    g_star: float
    #: $h^2 \Omega_{p,0}$, peak value of the power spectrum today
    omega_p0_h2: th.FloatArr2D
    #: $f_{p,0}$, peak frequency today in Hz
    f_p0: th.FloatArr2D
    #: $r_b$, ratio of the break frequencies
    rb: th.FloatArr2D
    #: $b$, spectral slope between the breaks
    b: th.FloatArr2D

    @classmethod
    def compute(
            cls,
            v_walls: th.FloatArr1D | None = None,
            alpha_ns: th.FloatArr1D | None = None,
            r_star: float = 0.1,
            T_star: float = 100.,
            g_star: float = DEFAULT_G_STAR,
            data_path: str | os.PathLike[str] = SSM_DATA_PATH,
            fit_path: str | os.PathLike[str] = SSM_FIT_PATH) -> "GH21dbplParams":
        r"""Compute the spectral parameters on a grid.

        :param v_walls: $v_{\text{wall}}$, wall speeds. Defaults to the grid of the SSM fit.
        :param alpha_ns: $\alpha_n$, transition strengths. Defaults to the grid of the SSM fit.
        :param r_star: $r_*$, Hubble-scaled mean bubble spacing
        :param T_star: $T_*$, transition temperature
        :param g_star: $g_*$, degrees of freedom
        :param data_path: Path to the SSM spectra, see :py:func:`cached_dbpl_fit`
        :param fit_path: Path to the cache file of the fit, see :py:func:`cached_dbpl_fit`
        :return: The spectral parameters
        """
        fit = cached_dbpl_fit(data_path=data_path, fit_path=fit_path)
        v_walls = fit.v_walls if v_walls is None else v_walls
        alpha_ns = fit.alpha_ns if alpha_ns is None else alpha_ns
        shape = (alpha_ns.size, v_walls.size)
        omega_p0_h2 = np.empty(shape)
        f_p0 = np.empty(shape)
        rb = np.empty(shape)
        b = np.empty(shape)
        for i, alpha_n in enumerate(alpha_ns):
            for j, v_wall in enumerate(v_walls):
                spectrum = GH21dbpl(
                    v_wall=v_wall, alpha=alpha_n, r_star=r_star, T_star=T_star, g_star=g_star,
                    data_path=data_path, fit_path=fit_path
                )
                omega_p0_h2[i, j] = spectrum.omega_peak_h2()
                f_p0[i, j] = spectrum.f_peak()
                rb[i, j] = spectrum.rb
                b[i, j] = spectrum.b
        return cls(
            v_walls=v_walls, alpha_ns=alpha_ns, r_star=r_star, T_star=T_star, g_star=g_star,
            omega_p0_h2=omega_p0_h2, f_p0=f_p0, rb=rb, b=b
        )

    @property
    def omega_p0(self) -> th.FloatArr2D:
        r"""$\Omega_{p,0}$, peak value of the power spectrum today, with $h$ of :py:mod:`pttools.omgw0.const`."""
        return self.omega_p0_h2 / H**2


@functools.cache
def _cached_dbpl_fit(data_path: Path, fit_path: Path) -> GH21dbplFit:
    """Implementation of :py:func:`cached_dbpl_fit`, which takes the paths as resolved :py:class:`pathlib.Path` objects.

    The paths are resolved in :py:func:`cached_dbpl_fit` so that the in-memory cache does not depend on their type.
    """
    fields = [field.name for field in dataclasses.fields(GH21dbplFit)]
    version = f"{ptplot_version()}-{pttools_version()}"
    if fit_path.exists():
        try:
            with np.load(fit_path) as data:
                if str(data["version"]) == version:
                    return GH21dbplFit(**{field: data[field] for field in fields})
                logger.info(
                    "The GH21dbpl fit in %s is for the versions %s, but the current versions are %s. Fitting again.",
                    fit_path, data["version"], version
                )
        except (OSError, KeyError, ValueError):
            logger.exception("Could not load the GH21dbpl fit from %s. Fitting again.", fit_path)
    logger.info("Fitting the GH21dbpl parameters to the SSM spectra. This takes a few seconds.")
    with np.load(data_path) as data:
        fit = fit_dbpl_to_ssm(data)
    # The file is written atomically, as multiple processes may be fitting simultaneously.
    tmp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(dir=fit_path.parent, suffix=".npz", delete=False) as file:
            tmp_path = Path(file.name)
            np.savez(file, version=version, **{field: getattr(fit, field) for field in fields})
        tmp_path.replace(fit_path)
    except OSError:
        logger.exception("Could not save the GH21dbpl fit to %s.", fit_path)
        if tmp_path is not None:
            tmp_path.unlink(missing_ok=True)
    return fit


def cached_dbpl_fit(
        data_path: str | os.PathLike[str] = SSM_DATA_PATH,
        fit_path: str | os.PathLike[str] = SSM_FIT_PATH) -> GH21dbplFit:
    r"""DBPL fit to the SSM spectra, see :py:func:`fit_dbpl_to_ssm`.

    The result is cached in memory and in ``fit_path``.
    The cache file is recreated when the version of PTPlot or PTtools changes.

    :param data_path: Path to the SSM spectra in the format of :py:data:`SSM_DATA_PATH`
    :param fit_path: Path to the cache file of the fit
    :return: The best-fit parameters
    """
    return _cached_dbpl_fit(data_path=Path(data_path).resolve(), fit_path=Path(fit_path).resolve())


def data_key(v_wall: float, alpha_n: float) -> str:
    r"""Key of the SSM spectrum of $v_{\text{wall}}$ and $\alpha_n$ in the format of :py:data:`SSM_DATA_PATH`.

    The values are written with :py:func:`str`, and the dots are replaced with underscores,
    e.g. ``vw0_4al0_01`` for $v_{\text{wall}} = 0.4$ and $\alpha_n = 0.01$.
    The values have to be exactly those of the grid of the data file, i.e. ``vw_list`` and ``alpha_list``.
    """
    return f"vw{v_wall}al{alpha_n}".replace(".", "_")


def data_points(data: NpzFile) -> tuple[th.FloatArr1D, th.FloatArr1D]:
    r"""$(v_{\text{wall}}, \alpha_n)$ points for which the data file has a spectrum.

    :param data: SSM spectra in the format of :py:data:`SSM_DATA_PATH`, opened with :py:func:`numpy.load`
    :return: $v_{\text{wall}}$ and $\alpha_n$ of the points
    """
    keys = set(data.files)
    points = [
        (v_wall, alpha_n)
        for v_wall in data["vw_list"] for alpha_n in data["alpha_list"]
        if data_key(v_wall, alpha_n) in keys
    ]
    v_walls, alpha_ns = np.array(points).T
    return v_walls, alpha_ns


def delta2(z: th.FloatArr1D, p_fit: th.FloatArr1D, p_ssm: th.FloatArr1D) -> np.float64:
    r"""$\delta_\mathcal{P}^2$, mean squared relative deviation of a fit from the SSM spectrum.

    $$\delta_\mathcal{P}^2 = \int \frac{dz}{z}
    \left( \frac{\hat{\mathcal{P}}_\text{gw}^\text{fit}(z) - \hat{\mathcal{P}}_\text{gw}^\text{ssm}(z)}
    {\hat{\mathcal{P}}_\text{gw}^\text{ssm}(z)} \right)^2$$
    :gowling_2021:`\ ` eq. B.1, evaluated for the best-fit parameters with the trapezoidal rule in $\ln z$.

    :param z: $z = kR_*$, in increasing order
    :param p_fit: $\hat{\mathcal{P}}_\text{gw}^\text{fit}(z)$, fitted spectrum
    :param p_ssm: $\hat{\mathcal{P}}_\text{gw}^\text{ssm}(z)$, SSM spectrum
    :return: $\delta_\mathcal{P}^2$
    """
    return np.trapezoid(((p_fit - p_ssm) / p_ssm)**2, np.log(z))


def fit_dbpl_to_ssm(
        data: NpzFile,
        zb0: float = 1.,
        zp0: float = 10.,
        b0: float = 1.) -> GH21dbplFit:
    r"""Fit the DBPL to the SSM spectra $\hat{\mathcal{P}}_\text{gw}(z)$.

    $$\hat{\mathcal{P}}_\text{gw}^\text{fit}(z) = \hat{\Omega}_p M(z / z_p, z_b / z_p, b)$$
    :gowling_2021:`\ ` eq. 2.15.
    For each $v_{\text{wall}}$ and $\alpha_n$, the points with $\hat{\mathcal{P}}_\text{gw} > \hat{\Omega}_p / 10$
    or $z < 3$ are fitted with the relative errors $\sigma = \hat{\mathcal{P}}_\text{gw}$,
    with $b \geq 0$ for $v_{\text{wall}} < c_s$ and $b \geq -1$ otherwise.
    These are the settings of ``fit_power_gw_scaled_to_obs_ssm.py`` of :gowling_2021:`\ `.

    Based on ``general_fit_function`` in ``parameter_dependence/fit_power_gw_scaled_to_obs_ssm.py``
    of the ``fisher_analysis`` repository of :gowling_2021:`\ `.

    :param data: SSM spectra in the format of :py:data:`SSM_DATA_PATH`, opened with :py:func:`numpy.load`.
        The file has to stay open during the fit, as the spectra are read from it one at a time.
    :param zb0: $z_{b,0}$, initial guess for $z_b$
    :param zp0: $z_{p,0}$, initial guess for $z_p$
    :param b0: $b_0$, initial guess for $b$
    :return: The best-fit parameters
    """
    v_walls = data["vw_list"]
    alpha_ns = data["alpha_list"]
    z = data["zs"]
    params = np.empty((alpha_ns.size, v_walls.size, 4))
    delta2_grid = np.empty((alpha_ns.size, v_walls.size))

    def model(z_: th.FloatArr1D, omp: float, zb: float, zp: float, b: float) -> th.FloatArr1D:
        return omp * M(s=z_ / zp, rb=zb / zp, b=b)

    for i, alpha_n in enumerate(alpha_ns):
        for j, v_wall in enumerate(v_walls):
            p_gw = data[data_key(v_wall, alpha_n)]
            peak = p_gw.max()
            fit_points = np.logical_or(p_gw > peak / 10, z < 3)  # noqa: PLR2004
            z_fit = z[fit_points]
            p_points = p_gw[fit_points]
            # The intermediate steps of the fit may go to parameters for which the model is invalid.
            with np.errstate(invalid="ignore"):
                params[i, j], _ = curve_fit(
                    model, z_fit, p_points,
                    p0=[peak, zb0, zp0, b0],
                    sigma=p_points,
                    bounds=([0, 0, 0, 0 if v_wall < CS0 else -1], np.inf),  # As in general_fit_function
                    maxfev=5000
                )
            delta2_grid[i, j] = delta2(z=z_fit, p_fit=model(z_fit, *params[i, j]), p_ssm=p_points)

    return GH21dbplFit(
        v_walls=v_walls, alpha_ns=alpha_ns,
        omega_p_hat=params[..., 0], zb=params[..., 1], zp=params[..., 2], b=params[..., 3],
        delta2=delta2_grid
    )


@njit(cache=True)
def m[T: FloatOrArr](rb: T | float, b: T | float) -> T:
    r"""Value $m$ used in the spectral shape function $M(s)$.

    $$m = \frac{9 r_b^4 + b}{r_b^4 + 1}$$
    :gowling_2021:`\ ` eq. 2.17.
    With $b = 1$, this reduces to
    :gw_pt_ssm:`\ ` p. 22.

    :param rb: $r_b$, ratio of the break frequencies
    :param b: $b$, spectral slope between the breaks
    :return: $m$
    """
    return (9 * rb**4 + b) / (rb**4 + 1)  # pyrefly: ignore[bad-return]


@njit(cache=True)
def M[T: FloatOrArr](s: T, rb: FloatOrArr, b: FloatOrArr = 1.) -> T:
    r"""Spectral shape of the GW power spectrum.

    $$M(s, r_b, b) = s^9
    \left( \frac{1 + r_b^4}{r_b^4 + s^4} \right)^\frac{9 - b}{4}
    \left( \frac{b + 4}{b + 4 - m + ms^2} \right)^\frac{b + 4}{2}$$
    This formula is a fit to the Sound Shell Model power spectrum.
    :gowling_2021:`\ ` eq. 2.16
    With $b = 1$, this reduces to
    :gw_pt_ssm:`\ ` eq. 5.7

    :param s: Frequency $s$ relative to the peak frequency
    :param rb: $r_b$, ratio of the break frequencies
    :param b: $b$ defines the spectral slope between the two breaks in the spectrum
    :return: Spectral shape $M(s, r_b, b)$
    """
    m_ = m(rb=rb, b=b)
    return (
        s**9  # pyrefly: ignore[bad-return]
        * ((1 + rb**4) / (rb**4 + s**4)) ** ((9 - b) / 4)
        * ((b + 4) / (b + 4 - m_ + m_ * s**2)) ** ((b + 4) / 2)
    )
