"""Tests for the utilities of the science module."""

import logging

import numpy as np
import pytest

from ptplot.science import const
from ptplot.science.utils import log_exceptions, log_range

logger: logging.Logger = logging.getLogger(__name__)

DEFAULT: np.ndarray = const.DEFAULT_BETA_TILDE_RANGE


def test_log_range_default() -> None:
    """Values within the default range should give the default range."""
    assert log_range(np.array([DEFAULT[1], DEFAULT[-2]]), DEFAULT) is DEFAULT
    assert log_range([np.array([DEFAULT[1]]), np.array([DEFAULT[-2], np.nan])], DEFAULT) is DEFAULT


def test_log_range_cover() -> None:
    """Values outside the default range should extend it, keeping its size."""
    x = [DEFAULT[0] / 10, DEFAULT[-1] * 10]
    arr = log_range(np.array(x), DEFAULT)
    assert arr.size == DEFAULT.size
    np.testing.assert_allclose(arr[[0, -1]], x, rtol=1e-12)


def test_log_range_size() -> None:
    """The size should change the number of points but not the endpoints."""
    arr = log_range(DEFAULT[1], DEFAULT, size=5)
    np.testing.assert_allclose(arr, np.logspace(np.log10(DEFAULT[0]), np.log10(DEFAULT[-1]), 5), rtol=1e-12)


def test_log_range_limits() -> None:
    """The given limits should be used even if the values are outside them."""
    x = np.array([DEFAULT[0] / 10, DEFAULT[-1] * 10])
    np.testing.assert_allclose(log_range(x, DEFAULT, size=3, range_min=10., range_max=1000.), [10., 100., 1000.])
    # Only one of the limits is given.
    arr = log_range(x, DEFAULT, range_min=10.)
    np.testing.assert_allclose(arr[[0, -1]], [10., x[-1]], rtol=1e-12)
    arr = log_range(x, DEFAULT, range_max=1000.)
    np.testing.assert_allclose(arr[[0, -1]], [x[0], 1000.], rtol=1e-12)


@pytest.mark.parametrize(
    "kwargs", [{"size": 1}, {"range_min": 0.}, {"range_min": 100., "range_max": 10.}, {"range_min": 1e6}])
def test_log_range_invalid(kwargs: dict) -> None:
    """Invalid sizes and limits should be rejected."""
    with pytest.raises(ValueError, match="must be"):
        log_range(DEFAULT[1], DEFAULT, **kwargs)


def test_log_exceptions(caplog: pytest.LogCaptureFixture) -> None:
    """The exceptions should be logged with their tracebacks instead of being raised."""
    with caplog.at_level(logging.ERROR, logger=__name__), log_exceptions(logger, "Failed to do %s", "something"):
        raise ValueError("Test error")
    assert len(caplog.records) == 1
    record = caplog.records[0]
    assert record.getMessage() == "Failed to do something"
    assert record.exc_info is not None
    assert isinstance(record.exc_info[1], ValueError)


def test_log_exceptions_no_exception(caplog: pytest.LogCaptureFixture) -> None:
    """Nothing should be logged if there is no exception."""
    with caplog.at_level(logging.ERROR, logger=__name__), log_exceptions(logger, "Failed"):
        pass
    assert not caplog.records


def test_log_exceptions_keyboard_interrupt() -> None:
    """Exceptions that are not subclasses of Exception should be raised, so that the script can be stopped."""
    with pytest.raises(KeyboardInterrupt), log_exceptions(logger, "Failed"):
        raise KeyboardInterrupt
