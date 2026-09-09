"""Comparison of the SNR values of two grids."""

import enum
import logging

from matplotlib.colors import Normalize, SymLogNorm
import numpy as np

from ptplot.science.snr.grid import SNRGrid
import ptplot.science.type_hints as th

logger = logging.getLogger(__name__)

#: Number of decades to include in a logarithmic color scale
DEFAULT_N_DECADES: int = 6


class ComparisonMethod(enum.StrEnum):
    """Ways of comparing the SNR values of two grids."""

    RELATIVE_DIFFERENCE = DEFAULT = "relative_difference"
    ABSOLUTE_DIFFERENCE = "absolute_difference"


def symlog_levels(
        values: th.FloatArr,
        n_decades: int = DEFAULT_N_DECADES) -> tuple[th.FloatArr1D | None, float]:
    r"""Compute symmetric logarithmic contour levels for values that can be of either sign.

    The levels span $n_\text{decades}$ decades below the largest absolute value,
    and the levels of the sign that does not occur in the values are omitted.

    :param values: Values to compute the levels for
    :param n_decades: Number of decades to cover
    :return: Contour levels, and the linear threshold below which the scale is linear.
        The levels are None, if the values are all zero or non-finite,
        and therefore cannot be drawn on a logarithmic scale.
    """
    finite = values[np.isfinite(values)]
    abs_max = np.max(np.abs(finite)) if finite.size else 0.
    if not abs_max:
        return None, 0.

    exp_max = int(np.ceil(np.log10(abs_max)))
    exp_min = exp_max - n_decades
    positive: th.FloatArr1D = np.logspace(exp_min, exp_max, n_decades + 1)

    levels: list[th.FloatArr1D] = [np.zeros(1)]
    if np.min(finite) < 0:
        levels.insert(0, -positive[::-1])
    if np.max(finite) > 0:
        levels.append(positive)
    return np.concatenate(levels), 10.**exp_min


class SNRGridComparison:
    """Comparison of the SNR values of two grids.

    The grids must have the same axes and ranges, so that they can be compared point by point.
    Therefore, the axes and their labels are provided by this class as well.
    The comparison is computed when the object is created.
    """

    def __init__(
            self,
            grid1: SNRGrid,
            grid2: SNRGrid,
            method: ComparisonMethod = ComparisonMethod.DEFAULT,
            label: str | None = None,
            n_decades: int = DEFAULT_N_DECADES):
        """Compare the SNR values of two grids.

        :param grid1: SNR grid of the reference
        :param grid2: SNR grid to compare to the reference
        :param method: How to compare the SNR values
        :param label: Label of the comparison, defaults to a label deduced from the method
            and the names of the grids
        :param n_decades: Number of decades to cover with a logarithmic color scale
        """
        if grid1.X_NAME != grid2.X_NAME or grid1.Y_NAME != grid2.Y_NAME:
            raise ValueError(
                "SNR grids must have the same axes. "
                f"Got: grid1=({grid1.X_NAME}, {grid1.Y_NAME}), ({grid2.X_NAME}, {grid2.Y_NAME})"
            )
        if grid1.x.shape != grid2.x.shape or grid1.y.shape != grid2.y.shape \
                or not np.allclose(grid1.x, grid2.x) or not np.allclose(grid1.y, grid2.y):
            raise ValueError("SNR grids must have the same ranges.")

        self.grid1: SNRGrid = grid1
        self.grid2: SNRGrid = grid2
        self.method: ComparisonMethod = method
        self.n_decades: int = n_decades

        # The axes of the grids are equal, as validated above.
        self.x: th.FloatArr1D = grid1.x
        self.y: th.FloatArr1D = grid1.y
        self.X_NAME: str = grid1.X_NAME
        self.Y_NAME: str = grid1.Y_NAME
        self.X_LABEL: str = grid1.X_LABEL
        self.Y_LABEL: str = grid1.Y_LABEL

        match method:
            case ComparisonMethod.RELATIVE_DIFFERENCE:
                self.snr_diff: th.FloatArr2D = \
                    (grid2.snr - grid1.snr) / np.maximum(grid1.snr, grid2.snr)
            case ComparisonMethod.ABSOLUTE_DIFFERENCE:
                self.snr_diff = grid2.snr - grid1.snr
            case _:
                raise ValueError(f"Unknown comparison method: {method}")

        self.label: str = self.default_label() if label is None else label

        #: Contour levels of the figure. None means that they are chosen automatically.
        self.levels: th.FloatArr1D | None = None
        #: Color scale of the figure. None means that it is chosen automatically.
        self.norm: Normalize | None = None
        if self.logarithmic:
            self.levels, linthresh = symlog_levels(self.snr_diff, n_decades)
            if self.levels is None:
                logger.warning(
                    "The SNR values of the grids \"%s\" and \"%s\" are identical, "
                    "so a logarithmic color scale cannot be used.",
                    grid1.name, grid2.name
                )
            else:
                self.norm = SymLogNorm(
                    linthresh=linthresh,
                    vmin=self.levels[0],
                    vmax=self.levels[-1]
                )

    @property
    def logarithmic(self) -> bool:
        """Whether the comparison should be drawn on a logarithmic color scale."""
        return self.method == ComparisonMethod.ABSOLUTE_DIFFERENCE

    def default_label(self) -> str:
        """Construct the label of the comparison from the method and the names of the grids."""
        name1 = self.grid1.name
        name2 = self.grid2.name
        match self.method:
            case ComparisonMethod.RELATIVE_DIFFERENCE:
                return (
                    rf"$\frac{{\text{{SNR}}_{{{name2}}} - \text{{SNR}}_{{{name1}}}}}"
                    rf"{{\max( \text{{SNR}}_{{{name1}}}, \text{{SNR}}_{{{name2}}} )}}$"
                )
            case ComparisonMethod.ABSOLUTE_DIFFERENCE:
                return rf"$\text{{SNR}}_{{{name2}}} - \text{{SNR}}_{{{name1}}}$"
            case _:
                raise ValueError(f"Unknown comparison method: {self.method}")
