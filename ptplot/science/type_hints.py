"""Type hints for PTPlot science module"""
import typing as tp

import numpy as np

# Todo: use the "type" keyword when Python 3.12 is the oldest supported version
ArrOrListOfArrs: tp.TypeAlias = np.ndarray | list[np.ndarray]
FloatOrArr: tp.TypeAlias = float | np.ndarray
FloatOrListOrNestedListOrArr: tp.TypeAlias = float | list[float] | list[list[float]] | np.ndarray
StrOrList: tp.TypeAlias = str | list[str]
StrOrListOrNestedList: tp.TypeAlias = str | list[str] | list[list[str]]
