"""Utilities for PTPlot."""

from pttools.utils.system import testing

__all__ = ["is_django", "is_django_or_testing"]

#: Whether running in the Django server.
#: This is set by ``ptplot_site.wsgi`` and ``ptplot_site.asgi``. Use :py:func:`is_django` to get this value.
_DJANGO: bool = False


def is_django() -> bool:
    """Get whether running in the Django server."""
    return _DJANGO


def is_django_or_testing() -> bool:
    """Get whether running in the Django server or running unit tests."""
    return _DJANGO or testing()
