"""Type hints for PTPlot science module"""

import numpy as np
from numpy.typing import NDArray

type ArrOrListOfArrs = NDArray | list[NDArray]
type FloatArr = NDArray[np.float64]
type FloatArr1D = np.ndarray[tuple[int], np.dtype[np.float64]]
type FloatArr2D = np.ndarray[tuple[int, int], np.dtype[np.float64]]
type FloatOrArr = float | FloatArr
type FloatOrListOrNestedListOrArr = FloatOrArr | list[float] | list[list[float]]
type StrOrList = str | list[str]
type StrOrListOrNestedList = str | list[str] | list[list[str]]
