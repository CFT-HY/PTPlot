"""Type hints for PTPlot science module."""

import numpy as np
from numpy.typing import NDArray

type ArrOrListOfArrs = NDArray | list[NDArray]
type FloatArr = NDArray[np.float64]
type FloatArr1D = np.ndarray[tuple[int], np.dtype[np.float64]]
type FloatArr1DOrListOfArr1D = FloatArr1D | list[FloatArr1D]
type FloatArr2D = np.ndarray[tuple[int, int], np.dtype[np.float64]]
type FloatArr2DOrListOfArr1D = FloatArr2D | list[FloatArr1D]
type FloatOrArr = float | FloatArr
type FloatOrArr1D = float | FloatArr1D
type FloatOrArr1D2D = float | FloatArr1D | FloatArr2D
type FloatOrArrOrListOfArr1D = FloatOrArr1D | list[FloatArr1D]
type FloatOrArrOrList1D2D = FloatOrArr1D2D | list[float] | list[list[float]] | list[FloatArr1D]
type IntArr1D = np.ndarray[tuple[int], np.dtype[np.int64]]
type StrList2D = list[list[str]]
type StrOrList = str | list[str]
type StrOrListOrNestedList = str | list[str] | StrList2D
