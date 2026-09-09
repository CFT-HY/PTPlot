r"""
Wall velocity comparison
========================

Compare the SNR results of a model with two different $v_\text{wall}$ for each spectrum engine.
"""

import logging

from examples.utils import save_fig
from ptplot.methods import setup_django

if __name__ == "__main__":
    setup_django()

from ptplot.models import Model
from ptplot.science.snr.grid_alpha_beta import SNRGridAlphaBeta
from ptplot.science.spectrum import Engine

logger = logging.getLogger(__name__)


def snr_grid(model: Model, engine: Engine, v_wall: float) -> SNRGridAlphaBeta:
    r"""Compute the SNR grid of a model with the wall velocity of the model overridden.

    :param model: Model to compute the grid for
    :param engine: Which power spectrum engine to use
    :param v_wall: Wall velocity $v_\text{wall}$
    :return: SNR grid
    """
    return model.snr_grid_alpha_beta(
        engine=engine,
        v_wall=v_wall,
        name=rf"v_\text{{wall}}={v_wall}"
    )


def main(
        slug="singlet_jonathan",
        v_wall1: float = 0.95,
        v_wall2: float = 0.99):
    r"""Compare the SNR values of the two wall velocities with each engine."""
    model = Model.objects.prefetch_related("scenarios", "scenarios__points").get(slug=slug)

    for engine in Engine:
        logger.info("Comparing v_wall=%s and v_wall=%s for %s with the %s engine.",
                    v_wall1, v_wall2, model.name, engine.name)
        try:
            grid1 = snr_grid(model, engine=engine, v_wall=v_wall1)
            grid2 = snr_grid(model, engine=engine, v_wall=v_wall2)
            fig = model.snr_comparison(grid1=grid1, grid2=grid2)
            save_fig(fig, f"{model.slug}_snr_comparison_v_wall_{engine}")
        except Exception as exc:
            logger.exception(
                "Failed to plot the v_wall comparison for %s with the %s engine",
                model.name, engine.name,
                exc_info=exc
            )


if __name__ == "__main__":
    main()
