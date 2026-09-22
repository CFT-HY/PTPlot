r"""
Power spectra of the engines
============================

Plot the GW power spectrum of a single parameter choice with each engine in the same figure.
"""

import logging

from examples.utils import save_fig
from ptplot.methods import setup_django

if __name__ == "__main__":
    setup_django()

from ptplot.models import ParameterChoice
from ptplot.science.spectrum import Engine

logger = logging.getLogger(__name__)


def main(slug: str = "singlet_jonathan", number: int = 121):
    """Plot the power spectra of a single parameter choice with each engine.

    :param slug: Slug of the model that the parameter choice belongs to
    :param number: Number of the parameter choice within the model
    """
    point: ParameterChoice = ParameterChoice.objects.select_related("model", "scenario").get(
        model__slug=slug, number=number
    )
    engines = Engine.engines(log=True)
    logger.info(
        "Plotting the power spectra of the point %s of %s with the engines %s.",
        point.number, point.model.name, engines)
    fig = point.power_spectrum_figure(engine=engines)
    save_fig(fig, f"{slug}_point_{number}_ps")


if __name__ == "__main__":
    main()
