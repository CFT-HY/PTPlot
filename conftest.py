"""Configuration for the pytest test suite.

Most of the hooks and fixtures are defined in :mod:`pttools.utils.pytest`, so that they are shared with PTtools.
Pytest finds them, as they are imported here.
"""

from pathlib import Path

from pttools.utils.pytest import (
    configure_testing,
    log_test_name_at_start,
    pytest_collection_modifyitems,
    pytest_sessionfinish,
    pytest_xdist_auto_num_workers,
)
import pytest

# The imports are used by pytest.
__all__ = [
    "log_test_name_at_start",
    "pytest_collection_modifyitems",
    "pytest_configure",
    "pytest_sessionfinish",
    "pytest_xdist_auto_num_workers",
]


def pytest_configure(config: pytest.Config) -> None:  # noqa: ARG001
    """Configure the test suite of PTPlot with :func:`pttools.utils.pytest.configure_testing`."""
    configure_testing(name="ptplot", log_dir=Path(__file__).resolve().parent / "logs")
