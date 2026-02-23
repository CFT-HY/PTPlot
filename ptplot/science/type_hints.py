"""Type hints for PTPlot science module"""

import numpy as np
from numpy.typing import NDArray

type ArrOrListOfArrs = NDArray | list[NDArray]
type FloatArr = NDArray[np.float64]
type FloatArr1D = np.ndarray[tuple[int], np.dtype[np.float64]]
type FloatArr1DOrListOfArr1D = FloatArr1D | list[FloatArr1D]
type FloatArr2D = np.ndarray[tuple[int, int], np.dtype[np.float64]]
type FloatOrArr = float | FloatArr
type FloatOrArr1D = float | FloatArr1D
type FloatOrArr1D2D = float | FloatArr1D | FloatArr2D
type FloatOrArrOrListOfArr1D = FloatOrArr1D | list[FloatArr1D]
type FloatOrArrOrList1D2D = FloatOrArr1D2D | list[float] | list[list[float]]
type StrOrList = str | list[str]
type StrOrListOrNestedList = str | list[str] | list[list[str]]
