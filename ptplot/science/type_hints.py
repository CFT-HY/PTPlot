import typing as tp

import numpy as np

FLOAT_OR_LIST_OR_NESTED_LIST_OR_ARR = tp.Union[float, tp.List[float], tp.List[tp.List[float]], np.ndarray]
STR_OR_LIST = tp.Union[str, tp.List[str]]
STR_OR_LIST_OR_NESTED_LIST = tp.Union[str, tp.List[tp.List[str]]]
ARR_OR_LIST_OF_ARRS = tp.Union[np.ndarray, tp.List[np.ndarray]]
