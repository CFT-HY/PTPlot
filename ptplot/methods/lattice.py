"""Methods for lattice simulations."""

from collections.abc import Iterable
import typing as tp

from pttools.lattice.params import LatticeRunParams

if tp.TYPE_CHECKING:
    from ptplot.models import Model, ParameterChoice

__all__ = ["find_closest_points", "lattice_label"]


def find_closest_points(model: "Model", runs: Iterable[LatticeRunParams]) -> "dict[str, ParameterChoice]":
    r"""Find the points of a model whose $\alpha$ is closest to the $\alpha_n$ of the lattice simulations.

    See :py:meth:`ptplot.models.model.Model.closest_point`.
    The points can be highlighted in the SNR figures, see :py:class:`ptplot.science.plot.snr.SNRFigure`.
    To highlight the parameters of the simulations instead, see :py:meth:`ptplot.models.model.Model.lattice_points`.

    :param model: Model whose points are searched
    :param runs: Parameters of the lattice runs
    :return: Labels of the lattice runs, see :py:func:`lattice_label`, and the closest points
    """
    return {lattice_label(run): model.closest_point(run.alpha_n) for run in runs}


def lattice_label(run: LatticeRunParams) -> str:
    """Label of a lattice run in the figures: its label if given, and otherwise its capitalised name.

    :param run: Parameters of the lattice run
    :return: Label of the run
    """
    return run.name.capitalize() if run.label is None else run.label
