r"""
Power spectra of the engines
============================

Plot the GW power spectrum of a single parameter choice with each engine in the same figure.
"""

import logging
import typing as tp

from matplotlib.figure import Figure

from examples.utils import save_and_show_figs
from ptplot.methods import setup_django

if __name__ == "__main__":
    setup_django()

from ptplot.models import ParameterChoice
from ptplot.science.spectrum import Engine

logger: logging.Logger = logging.getLogger(__name__)


def plot_spectra(slug: str, number: int, engine: Engine | str | tp.Iterable[Engine]) -> Figure:
    """Plot the power spectra of a single parameter choice with each engine.

    :param slug: Slug of the model that the parameter choice belongs to
    :param number: Number of the parameter choice within the model
    :param engine: Engine or engines to model the spectrum with
    """
    point: ParameterChoice = ParameterChoice.objects.select_related("model", "scenario").get(
        model__slug=slug, number=number
    )
    logger.info(
        "Plotting the power spectra of the point %s of %s with the engines %s.",
        point.number, point.model.name, engine)
    return point.power_spectrum_figure(engine=engine)


def main() -> None:
    """Plot spectra of the selected points"""
    slug = "singlet_jonathan"
    numbers = [61, 121]
    engines = Engine.engines(log=True, strong=False)
    save_and_show_figs(
        {f"{slug}_point_{number}_ps": plot_spectra(slug=slug, number=number, engine=engines) for number in numbers}
    )


if __name__ == "__main__":
    main()
