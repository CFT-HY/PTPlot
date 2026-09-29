"""Configuration for the pytest test suite."""

import logging
from pathlib import Path

from pttools.logging import setup_logging
import pytest

logger: logging.Logger = logging.getLogger(__name__)


def pytest_configure(config: pytest.Config) -> None:  # noqa: ARG001
    """Set up logging for the test suite."""
    setup_logging(name="ptplot", log_dir=Path(__file__).resolve().parent / "logs")


@pytest.fixture(autouse=True)
def log_test_name_at_start(request: pytest.FixtureRequest) -> None:
    """
    Before starting a test, log its name.

    This makes it easier to retrieve the logs for a specific test.
    """
    logger.info("=" * 20 + request.node.nodeid + "=" * 20)
