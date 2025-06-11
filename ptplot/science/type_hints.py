import typing as tp

import numpy as np

# Todo: use the "type" keyword when Python 3.12 is the oldest supported version
FloatOrListOrNestedLisOrArr: tp.TypeAlias = tp.Union[float, tp.List[float], tp.List[tp.List[float]], np.ndarray]
StrOrList: tp.TypeAlias = tp.Union[str, tp.List[str]]
StrOrListOrNestedList: tp.TypeAlias = tp.Union[str, tp.List[str], tp.List[tp.List[str]]]
ArrOrListOfArrs: tp.TypeAlias = tp.Union[np.ndarray, tp.List[np.ndarray]]
