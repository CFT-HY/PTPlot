r"""
Singlet scalar SNR figures
==========================

This script generates the SNR figures for the singlet scalar model and the $Z_2$-symmetric singlet scalar model.
Running this script can take several hours.

The SNR figures of the engines of :py:data:`GRID_ENGINES` are drawn as the subplots of a single figure,
and the SNR grids of the other engines are computed only for the interactive figures.
The points of a model are drawn as a single set, i.e. they are not grouped by scenario.
The SNR grids are computed with the mean $T_*$ of the points of the model instead of the $T_*$ of the model,
see :py:meth:`ptplot.models.model.Model.point_T_star`.
The range of $\alpha_n$ of the $(\alpha_n, \beta/H_*)$ figures is limited to $\alpha_n \leq 1$ by default.
The SNR grids of the non-default engines are compared to that of the default engine in a single figure.
The histograms of the SNR values of the points include all the engines.

The points whose $\alpha_n$ is closest to those of the lattice simulations of :correia_2025:`\ `
(see :py:data:`pttools.lattice.chrw25.CHRW25_RUNS`) are highlighted in the SNR figures.
For each of these points, the GW power spectra of the simulation are compared to those of the engines,
see :py:func:`ptplot.science.plot.lattice.lattice_figure`.
The lattice spectra are drawn only if the data of the simulations is available,
see :py:func:`pttools.lattice.chrw25.data_dir`.

The figures are saved in the ``singlets`` subdirectory of the directory of each file format,
e.g. ``png/singlets``, and the interactive versions of the SNR figures of all the engines as HTML files
in ``html/singlets``, see :py:meth:`ptplot.science.plot.snr.SNRFigure.plotly_html`.
The settings can be changed with the command-line arguments, see ``python -m examples.snr.singlets --help``,
or with the arguments of :py:func:`main`.
"""

import argparse
import logging

from matplotlib.figure import Figure
from pttools.lattice import CHRW25_RUNS, load_chrw25_runs

from examples.utils import save_model_fig, save_model_html
from ptplot.methods import setup_django

if __name__ == "__main__":
    setup_django()

from ptplot.methods import Statistic, n_workers
from ptplot.models import Model
from ptplot.science.plot.lattice import lattice_figures
from ptplot.science.snr.grid import GridAxes, SNRGrid
from ptplot.science.snr.grid_comparison import engine_comparisons
from ptplot.science.spectrum import Engine
from ptplot.science.utils import log_exceptions

logger: logging.Logger = logging.getLogger(__name__)

#: Slugs of the singlet scalar models
SLUGS: tuple[str, ...] = ("singlet_jonathan", "singlet_jonathan_z2")
#: Engines whose SNR figures are drawn as the subplots of a single figure
GRID_ENGINES: tuple[Engine, ...] = (Engine.CosWG20bpl, Engine.GH21dbpl, Engine.CosWG24dbpl, Engine.SSM)
#: Subdirectory of the figures within the directory of each file format
SUBDIR: str = "singlets"
#: Default maximum $\alpha_n$ of the $(\alpha_n, \beta/H_*)$ figures
ALPHA_N_MAX: float = 1.


def create_figures(
        model: Model,
        alpha_n_max: float | None = ALPHA_N_MAX,
        T_star_statistic: Statistic = Statistic.MEAN,  # noqa: N803
        histogram_coswg24bpl: bool = True,
        max_workers: int = 1) -> None:
    r"""Create the SNR figures and the histogram of a model.

    :param model: Model whose figures are created
    :param alpha_n_max: Maximum $\alpha_n$ of the $(\alpha_n, \beta/H_*)$ figures,
        or None for the default range, which covers all the points
    :param T_star_statistic: Which statistic of the $T_*$ of the points to use for the SNR grids
    :param histogram_coswg24bpl: Whether to include CosWG24bpl in the histogram
    :param max_workers: Maximum number of worker processes
    """
    T_star = model.point_T_star(T_star_statistic)
    logger.info("Using the %s T_star=%.3f GeV of the points of %s.", T_star_statistic, T_star, model.name)
    highlights = lattice_highlights(model)
    axes = GridAxes(alpha_n_max=alpha_n_max)

    grids: dict[str, dict[Engine, SNRGrid]] = {"snr_alpha_beta": {}, "snr_ubarf_rstar": {}}
    for engine in Engine.engines(fast=True, log=True):
        for name, grid_func in (
                ("snr_alpha_beta", model.snr_grid_alpha_beta),
                ("snr_ubarf_rstar", model.snr_grid_ubarf_rstar)):
            with log_exceptions(logger, "Failed to plot %s_%s for %s", name, engine, model.name):
                grid = grid_func(
                    engine=engine, T_star=T_star, axes=axes, max_workers=max_workers, by_scenario=False
                )
                grids[name][engine] = grid
                save_model_html(
                    model.snr_figure(grid, highlights=highlights).plotly_html(), model, f"{name}_{engine}",
                    subdir=SUBDIR
                )

    for name, name_grids in grids.items():
        grid_list = [name_grids[engine] for engine in GRID_ENGINES if engine in name_grids]
        for filled in (False, True):
            fig_name = f"{name}_filled" if filled else name
            with log_exceptions(logger, "Failed to plot %s for %s", fig_name, model.name):
                save(model.snr_figure_grid(grid_list, filled=filled, highlights=highlights), model, fig_name)

    with log_exceptions(logger, "Failed to plot snr_comparison for %s", model.name):
        comparisons = engine_comparisons({
            engine: grid for engine, grid in grids["snr_alpha_beta"].items() if engine in GRID_ENGINES
        })
        save(
            model.snr_comparison_grid(list(comparisons.values()), highlights=highlights, ncols=len(comparisons)),
            model, "snr_comparison"
        )

    with log_exceptions(logger, "Failed to plot snr_histogram for %s", model.name):
        engines = [
            engine for engine in Engine.engines(fast=True)
            if histogram_coswg24bpl or engine != Engine.CosWG24bpl
        ]
        save(model.snr_histogram(engines=engines), model, "snr_histogram")


def lattice_highlights(model: Model) -> dict[str, int]:
    r"""Find the points of a model whose $\alpha_n$ is closest to those of the lattice simulations.

    :param model: Model whose points are searched
    :return: Names of the simulations, and the indices of the closest points in the SNR grids
    """
    return {
        params.name.capitalize(): model.point_index(model.closest_point(params.alpha_n))
        for params in CHRW25_RUNS.values()
    }


def save(fig: Figure, model: Model, name: str) -> None:
    """Save a figure of a model in the subdirectory :py:data:`SUBDIR` of the directory of each file format."""
    save_model_fig(fig, model, name, subdir=SUBDIR)


def main(
        alpha_n_max: float | None = ALPHA_N_MAX,
        T_star_statistic: Statistic | str = Statistic.MEAN,  # noqa: N803
        histogram_coswg24bpl: bool = True,
        lattice_coswg24bpl: bool = True) -> None:
    r"""Create the figures of the singlet scalar models.

    :param alpha_n_max: Maximum $\alpha_n$ of the $(\alpha_n, \beta/H_*)$ figures,
        or None for the default range, which covers all the points
    :param T_star_statistic: Which statistic of the $T_*$ of the points to use for the SNR grids,
        e.g. ``"mean"`` or ``"median"``
    :param histogram_coswg24bpl: Whether to include CosWG24bpl in the histograms
    :param lattice_coswg24bpl: Whether to include CosWG24bpl in the comparisons with the lattice simulations
    """
    T_star_statistic = Statistic(T_star_statistic)  # noqa: N806
    # This is a heavy computation, so you may want to limit the number of workers on a shared system.
    max_workers = n_workers()
    logger.info("Creating the singlet figures with %d parallel workers.", max_workers)
    runs = load_chrw25_runs(missing_ok=True)
    lattice_engines = [
        engine for engine in Engine.engines(fast=True) if lattice_coswg24bpl or engine != Engine.CosWG24bpl
    ]
    for model in Model.objects.filter(slug__in=SLUGS).prefetch_related("points"):
        logger.info("##### Processing model: %s", model.name)
        create_figures(
            model,
            alpha_n_max=alpha_n_max,
            T_star_statistic=T_star_statistic,
            histogram_coswg24bpl=histogram_coswg24bpl,
            max_workers=max_workers
        )
        for name, fig in lattice_figures(model, runs, engines=lattice_engines).items():
            save(fig, model, f"lattice_{name}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create the SNR figures for the singlet scalar models.")
    parser.add_argument(
        "--alpha-n-max", type=float, default=ALPHA_N_MAX,
        help=f"maximum alpha_n of the SNR alpha-beta figures (default: {ALPHA_N_MAX})"
    )
    parser.add_argument(
        "--median", action="store_true",
        help="compute the SNR grids with the median T_star of the points instead of the mean"
    )
    parser.add_argument(
        "--no-histogram-coswg24bpl", action="store_true",
        help="leave CosWG24bpl out of the histograms"
    )
    parser.add_argument(
        "--no-lattice-coswg24bpl", action="store_true",
        help="leave CosWG24bpl out of the comparisons with the lattice simulations"
    )
    args = parser.parse_args()
    main(
        alpha_n_max=args.alpha_n_max,
        T_star_statistic=Statistic.MEDIAN if args.median else Statistic.MEAN,
        histogram_coswg24bpl=not args.no_histogram_coswg24bpl,
        lattice_coswg24bpl=not args.no_lattice_coswg24bpl
    )
