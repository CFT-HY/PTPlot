"""Tests for the axis ticks."""

import numpy as np

from ptplot.science.plot.ticks import make_minor_ticks


def test_minor_ticks() -> None:
    """There should be minor ticks at 1-9 times the powers of ten within the full decades."""
    ticks = make_minor_ticks(-1, 1)
    np.testing.assert_allclose(10**ticks, [*np.arange(1, 10) / 10, *np.arange(1, 10)], rtol=1e-12)


def test_minor_ticks_no_decades() -> None:
    """A range without full decades should have no minor ticks."""
    assert make_minor_ticks(1, 1).size == 0
    assert make_minor_ticks(1, 0).size == 0
