"""Configuration for the pytest test suite"""

import logging
import os.path

import pytest

from pttools.logging import setup_logging

logger = logging.getLogger(__name__)


def pytest_configure(config: pytest.Config) -> None:
    setup_logging(name="ptplot", log_dir=os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs"))


@pytest.fixture(scope="function", autouse=True)
def log_test_name_at_start(request):
    """
    Before starting a test, log its name.
    This makes it easier to retrieve the logs for a specific test.
    """
    logger.info("=" * 20 + request.node.nodeid + "=" * 20)
