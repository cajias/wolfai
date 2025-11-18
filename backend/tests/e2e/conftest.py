"""Pytest configuration for e2e/BDD tests."""

import pytest


def pytest_configure(config: pytest.Config) -> None:
    """Register custom markers."""
    config.addinivalue_line("markers", "e2e: mark test as end-to-end test")
    config.addinivalue_line("markers", "bdd: mark test as BDD/Cucumber test")
