"""Parallel utilities."""

from pttools.speedup import MAX_WORKERS_DEFAULT
from pttools.utils import IS_CFT_BIG_MACHINE

from ptplot.science.const import DEFAULT_ALPHA_N_RANGE


def n_workers(n_tasks: int = DEFAULT_ALPHA_N_RANGE.size):
    """Get the optimal number of parallel workers.

    Some of the computations are quite heavy,
    so one may want to limit the number of parallel workers on a shared system.
    """
    if IS_CFT_BIG_MACHINE:
        n_batches = 3
        return min(
            MAX_WORKERS_DEFAULT,
            n_tasks // n_batches + int(bool(n_tasks % n_batches)),
        )
    return MAX_WORKERS_DEFAULT
