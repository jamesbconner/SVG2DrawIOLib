"""Pytest configuration and shared fixtures."""

import logging

import pytest


@pytest.fixture(autouse=True)
def _setup_logging() -> None:
    """Configure logging for tests."""
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(levelname)s - %(name)s - %(message)s",
    )
