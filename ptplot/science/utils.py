import typing as tp

import numpy as np

import ptplot.science.type_hints as th


def atleast_2d(*args: tp.Union[th.FLOAT_OR_LIST_OR_NESTED_LIST_OR_ARR]) -> tp.Union[th.ARR_OR_LIST_OF_ARRS, tp.List[th.ARR_OR_LIST_OF_ARRS]]:
    """Convert a scalar, 1D array or 2D array into a 2D numpy array.

    Similar to numpy.atleast_2d, but supports nested lists with varying lenghts.
    """
    num_args = len(args)
    if not num_args:
        raise ValueError("At least one argument is required.")
    if num_args == 1:
        return atleast_2d_single(args[0])
    return [atleast_2d_single(values) for values in args]


def atleast_2d_single(values: tp.Union[th.FLOAT_OR_LIST_OR_NESTED_LIST_OR_ARR]) -> th.ARR_OR_LIST_OF_ARRS:
    if isinstance(values, np.ndarray):
        return np.atleast_2d(values)
    if np.isscalar(values):
        return np.array([[values]])
    if np.isscalar(values[0]):
        return np.array([values])
    # If the data has a regular shape, convert it to a 2D numpy array.
    if np.all([len(sub_values) == len(values[0]) for sub_values in values]):
        return np.array(values)
    return [np.array(sub_values) for sub_values in values]
