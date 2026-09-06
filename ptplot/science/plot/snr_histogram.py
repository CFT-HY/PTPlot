# import typing as tp

from matplotlib.figure import Figure
import numpy as np

from ptplot.science import const
from ptplot.science.mission_profile import DEFAULT_MISSION_PROFILE, MissionProfile
from ptplot.science.plot.utils import add_text, watermark
from ptplot.science.snr import snr_point
from ptplot.science.spectrum.engine import ENGINE_NAMES, Engine
import ptplot.science.type_hints as th

# if tp.TYPE_CHECKING:
#     from ptplot.models.parameter_choice import ParameterChoice


def snr_histogram(
        # points: "ParameterChoice",
        v_wall: th.FloatArr1D,
        alpha_n: th.FloatArr1D,
        beta_over_H: th.FloatArr1D,
        T_star: th.FloatArr1D,
        g_star: th.FloatArr1D,
        adiabatic_ratio: float = const.DEFAULT_ADIABATIC_RATIO,
        labels: th.StrOrListOrNestedList | None = None,
        titles: th.StrOrList | None = None,
        mission_profile: MissionProfile = DEFAULT_MISSION_PROFILE,
        engines: list[Engine] | None = None,
        n_bins_min: int = 5) -> Figure:
    """Histogram of signal-to-noise ratios (SNR) for a set of points in the parameter space

    https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.hist.html
    https://matplotlib.org/stable/gallery/statistics/histogram_histtypes.html
    https://matplotlib.org/stable/gallery/statistics/histogram_multihist.html
    """
    fig = Figure()
    ax = fig.add_subplot()

    if engines is None:
        engines = list(Engine)

    snr = np.empty((alpha_n.size, len(engines)))
    for i_engine, engine in enumerate(engines):
        for i_point in range(alpha_n.size):
            snr[i_point, i_engine], _ = snr_point(
                x=alpha_n[i_point],
                y=beta_over_H[i_point],
                T_star=T_star[i_point],
                g_star=g_star[i_point],
                v_wall=v_wall[i_point],
                adiabatic_ratio=adiabatic_ratio,
                f_min=mission_profile.f_min,
                f_max=mission_profile.f_max,
                mission_profile=mission_profile,
                engine=engine
            )

    snr_finite = np.isfinite(snr)
    snr[~snr_finite] = np.nan
    snr_finite_count = snr_finite.sum(axis=0)

    log10_snr_min = np.log10(np.nanmin(snr))
    log10_snr_max = np.log10(np.nanmax(snr))
    if log10_snr_max - log10_snr_min > n_bins_min:
        log10_snr_min = int(log10_snr_min)
        log10_snr_max = int(log10_snr_max) + 1
        n_bins = log10_snr_max - log10_snr_min + 1
    else:
        n_bins = max(n_bins_min, v_wall.size // 20)
    bins = np.logspace(log10_snr_min, log10_snr_max, n_bins)
    # print(bins)

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
    add_text(fig, watermark())
    ax.set_xscale("log")
    ax.set_xlabel("SNR")
    ax.set_ylabel("Number of points")
    ax.legend()
    fig.tight_layout()
    return fig
