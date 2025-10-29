import pytest

from tests.tools.pl.test_mcp_mock import MockMCPSession


@pytest.fixture
async def mock_session():
    """Provide a mock MCP session for testing."""
    return MockMCPSession()
