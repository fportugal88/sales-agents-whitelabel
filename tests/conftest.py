"""Pytest configuration and shared fixtures."""

import pytest

from src.utils.logger import configure_logging

# Configure logging for tests
configure_logging(log_level="DEBUG")


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    import asyncio

    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

