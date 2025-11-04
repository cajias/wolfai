"""Shared pytest configuration for all tests."""
import pytest


def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", "requires_swipl: mark test as requiring SWI-Prolog"
    )


def pytest_collection_modifyitems(config, items):
    """Skip tests that require SWI-Prolog if it's not available."""
    try:
        from pyswip import Prolog  # noqa: F401
        swipl_available = True
    except Exception:
        swipl_available = False

    if not swipl_available:
        skip_swipl = pytest.mark.skip(reason="SWI-Prolog not available")
        for item in items:
            # Skip any test that has "prolog" in the path or requires_swipl marker
            if "test_prolog" in str(item.fspath) or "requires_swipl" in item.keywords:
                item.add_marker(skip_swipl)


# Import mock session after skip logic is set up
try:
    from tests.tools.pl.test_mcp_mock import MockMCPSession
except ImportError:
    MockMCPSession = None


@pytest.fixture
async def mock_session():
    """Provide a mock MCP session for testing."""
    if MockMCPSession is None:
        pytest.skip("MockMCPSession not available")
    return MockMCPSession()
