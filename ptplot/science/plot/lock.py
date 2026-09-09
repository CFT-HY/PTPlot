"""Locking for the thread-unsafe parts of Matplotlib.

Matplotlib is not thread-safe.
Both the global ``rcParams``, which are modified by :func:`matplotlib.rc_context`,
and the mathtext parser, which is shared by all figures, are mutated when figures are created and rendered.
A page of PTPlot contains several figures, which the browser requests simultaneously,
and which the web server therefore renders in parallel threads.
This corrupts the shared state of Matplotlib and results in random errors such as::

    ValueError: ParseException: exception raised in parse action (at char 0), (line:1, col:1)

Therefore, the creation and rendering of the figures has to be serialised with the lock of this module.
"""

import functools
import threading
import typing as tp

#: Global lock for Matplotlib.
#: This is re-entrant so that the locked functions can call each other.
MATPLOTLIB_LOCK = threading.RLock()


def matplotlib_lock[**P, R](func: tp.Callable[P, R]) -> tp.Callable[P, R]:
    """Serialise the calls of the decorated function with the :data:`MATPLOTLIB_LOCK`."""
    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        with MATPLOTLIB_LOCK:
            return func(*args, **kwargs)
    return wrapper
