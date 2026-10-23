"""SNR histograms."""

# import typing as tp

from matplotlib.figure import Figure
import numpy as np
from pttools.export import Exporter
from pttools.speedup import MAX_WORKERS_DEFAULT

from ptplot.science import const
from ptplot.science.noise import Noise
from ptplot.science.plot.lock import matplotlib_lock
from ptplot.science.plot.utils import add_text, watermark
from ptplot.science.snr.points import snr_points
from ptplot.science.spectrum.engine import Engine
from ptplot.science.spectrum.engines import ENGINE_NAMES
from ptplot.science.spectrum.ssm import SSMSettings
import ptplot.science.type_hints as th

# if tp.TYPE_CHECKING:
#     from ptplot.models.parameter_choice import ParameterChoice

#: Default minimum number of bins of the histograms
N_BINS_MIN: int = 5
#: Default number of points per bin, which determines the number of bins
#: when the SNR values span at most :py:data:`N_BINS_MIN` decades, see :py:func:`snr_histogram_figure`
POINTS_PER_BIN: int = 10


def snr_histogram(
        # points: "ParameterChoice",
        v_wall: th.FloatArr1D,
        alpha_n: th.FloatArr1D,
        beta_tilde: th.FloatArr1D,
        T_star: th.FloatArr1D,
        g_star: th.FloatArr1D,
        adiabatic_index: float = const.DEFAULT_ADIABATIC_INDEX,
        labels: th.StrOrListOrNestedList | None = None,  # noqa: ARG001
        titles: th.StrOrList | None = None,  # noqa: ARG001
        noise: Noise | None = None,
        engines: list[Engine] | None = None,
        n_bins_min: int = N_BINS_MIN,
        points_per_bin: int = POINTS_PER_BIN,
        legacy_nucleation_cs_max: bool = const.DEFAULT_LEGACY_NUCLEATION_CS_MAX,
        exporter: Exporter | None = None,
        ssm_settings: SSMSettings | None = None,
        max_workers: int = MAX_WORKERS_DEFAULT) -> Figure:
    r"""Histogram of signal-to-noise ratios (SNR) for a set of points in the parameter space.

    The SNR values are computed in parallel with :py:func:`ptplot.science.snr.points.snr_points`,
    and the histogram is drawn with :py:func:`snr_histogram_figure`.
    The Matplotlib lock is held only while drawing, so that the computation does not block other figures,
    see :py:mod:`ptplot.science.plot.lock`.

    https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.hist.html
    https://matplotlib.org/stable/gallery/statistics/histogram_histtypes.html
    https://matplotlib.org/stable/gallery/statistics/histogram_multihist.html

    :param n_bins_min: Minimum number of bins, see :py:func:`snr_histogram_figure`
    :param points_per_bin: Number of points per bin, see :py:func:`snr_histogram_figure`
    :param legacy_nucleation_cs_max:
        Use legacy $\max(v_{\text{wall}}, c_s)$ in $\tilde{\beta} \leftrightarrow r_*$ conversion
    :param exporter: Exporter to which the computed spectra are added, e.g. for saving them to an HDF5 file.
        Only the spectra of the engines that support exporting are added,
        see :py:meth:`ptplot.science.spectrum.base.PowerSpectrum.record`.
    :param ssm_settings: Accuracy settings of the PTtools spectra of the SSM engine
    :param max_workers: Maximum number of worker processes or threads
    """
    if engines is None:
        engines = list(Engine)

    snr = snr_points(
        v_wall=v_wall, alpha_n=alpha_n, beta_tilde=beta_tilde, T_star=T_star, g_star=g_star,
        engines=engines, adiabatic_index=adiabatic_index, noise=noise,
        legacy_nucleation_cs_max=legacy_nucleation_cs_max, exporter=exporter, ssm_settings=ssm_settings,
        max_workers=max_workers
    )
    return snr_histogram_figure(snr, engines, n_bins_min=n_bins_min, points_per_bin=points_per_bin)


@matplotlib_lock
def snr_histogram_figure(
        snr: th.FloatArr2D,
        engines: list[Engine],
        n_bins_min: int = N_BINS_MIN,
        points_per_bin: int = POINTS_PER_BIN) -> Figure:
    """Draw the histogram of precomputed signal-to-noise ratios (SNR).

    The bins are logarithmic.
    If the SNR values span more than ``n_bins_min`` decades, there is a bin for each decade.
    Otherwise, the number of bins is the number of points divided by ``points_per_bin``,
    but at least ``n_bins_min``.

    :param snr: SNR values [point, engine], e.g. from :py:func:`ptplot.science.snr.points.snr_points`.
        The non-finite values are ignored.
    :param engines: Engines of the SNR values
    :param n_bins_min: Minimum number of bins
    :param points_per_bin: Number of points per bin, when there is not a bin for each decade
    :return: SNR histogram figure
    """
    fig = Figure()
    ax = fig.add_subplot()

    snr = snr.copy()
    snr_finite = np.isfinite(snr)
    snr[~snr_finite] = np.nan
    snr_finite_count = snr_finite.sum(axis=0)

    log10_snr_min = np.log10(np.nanmin(snr))
    log10_snr_max = np.log10(np.nanmax(snr))
    if log10_snr_max - log10_snr_min > n_bins_min:
        # The edges are rounded outwards to whole decades, so that all the values are within them,
        # also those below 1, whose logarithms are negative.
        log10_snr_min = int(np.floor(log10_snr_min))
        log10_snr_max = int(np.ceil(log10_snr_max))
        # A bin for each decade
        n_bins = log10_snr_max - log10_snr_min
    else:
        n_bins = max(n_bins_min, snr.shape[0] // points_per_bin)
    # The bins are defined by their edges, of which there is one more than bins.
    bins = np.logspace(log10_snr_min, log10_snr_max, n_bins + 1)

    ax.hist(
        snr,
        bins=bins,  # type: ignore[arg-type]  # Matplotlib does accept an array of bin edges.
        label=
            # Add number of points to the labels if all points were not solved by all engines.
            [f"{ENGINE_NAMES[engine]}" for i, engine in enumerate(engines)]
            if np.all(snr_finite_count == snr_finite_count[0]) else
            [f"{ENGINE_NAMES[engine]}, n={snr_finite_count[i]}" for i, engine in enumerate(engines)],
        # log=True,  # This only affects the y-axis
        # histtype="bar",
        # histtype="stepfilled",
        histtype="step",
        stacked=False,
        fill=False,
        # align="mid",
        # rwidth=0.8,
        alpha=0.5,
        linewidth=2,
        # color=[engine.spectrum.COLOR for engine in engines]
    )
    ax.set_xscale("log")
    ax.set_xlabel("SNR")
    ax.set_ylabel("Number of points")
    ax.legend()
    add_text(ax, watermark())
    return fig
