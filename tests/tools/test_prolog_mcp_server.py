"""Tests for the Prolog MCP server."""

import pytest
import pytest_asyncio
from unittest.mock import Mock, AsyncMock, patch
from mcp.server.fastmcp import FastMCP
from src.wolfai.tools.pl.prolog_mcp_server import PrologMCPServer, create_prolog_server
import swiplserver
import asyncio


def create_mock_thread():
    """Create a mock Prolog thread with basic functionality."""
    mock = Mock()
    mock.query.return_value = [{}]  # Default success response
    return mock


def create_mock_mqi():
    """Create a mock Prolog MQI."""
    mock = Mock()
    mock.create_thread.return_value = create_mock_thread()
    return mock


@pytest_asyncio.fixture
async def mock_prolog():
    """Create a mock SWI-Prolog instance."""
    with patch('swiplserver.PrologMQI', return_value=create_mock_mqi()):
        thread = create_mock_thread()
        yield thread


@pytest_asyncio.fixture
async def prolog_server(mock_prolog):
    """Create a PrologMCPServer instance with mocked Prolog."""
    server = PrologMCPServer()
    await server.initialize()  # Initialize the server
    server._prolog = mock_prolog  # Override with our mock
    server._initialized = True  # Ensure initialized flag is set
    yield server
    await server.cleanup()


@pytest.mark.asyncio
async def test_server_initialization():
    """Test server creation and initialization."""
    with patch('src.wolfai.tools.pl.prolog_mcp_server.PrologMCPServer') as mock_prolog_server:
        # Configure mock
        mock_instance = AsyncMock()
        mock_instance.initialize = AsyncMock()
        mock_instance.cleanup = AsyncMock()
        mock_prolog_server.return_value = mock_instance
        
        mcp = await create_prolog_server()
        assert isinstance(mcp, FastMCP)
        assert mcp.name == "Prolog MCP Server"
        
        # Check that required methods are registered
        assert hasattr(mcp, '_cleanup_handler')
        
        # Check that tools are registered
        assert hasattr(mcp, 'tool')
        assert callable(getattr(mcp, 'tool'))


@pytest.mark.asyncio
async def test_consult_tool(prolog_server, mock_prolog):
    """Test the consult tool for loading Prolog code."""
    code = """
    % Facts
    human(socrates).
    mortal(X) :- human(X).
    """
    
    result = await prolog_server.consult(code=code)
    
    # Check that the code was sent to Prolog
    mock_prolog.query.assert_called()
    assert result["success"] is True
    assert result.get("error") is None


@pytest.mark.asyncio
async def test_query_tool(prolog_server, mock_prolog):
    """Test the query tool for executing Prolog queries."""
    # Set up mock to return specific solutions
    mock_prolog.query.return_value = [{"X": "socrates"}]
    
    result = await prolog_server.query(query="mortal(X)")
    
    # Verify the query was executed
    mock_prolog.query.assert_called_with("mortal(X)")
    assert result["success"] is True
    assert len(result["solutions"]) == 1
    assert result["solutions"][0]["X"] == "socrates"


@pytest.mark.asyncio
async def test_prolog_error_handling(prolog_server, mock_prolog):
    """Test handling of Prolog execution errors."""
    # Simulate a Prolog error
    mock_prolog.query.side_effect = Exception("Syntax error")
    
    result = await prolog_server.query(query="invalid_query")
    
    assert result["success"] is False
    assert "syntax error" in result["error"].lower()
    assert result["solutions"] == []


@pytest.mark.asyncio
async def test_multiple_queries(prolog_server, mock_prolog):
    """Test executing multiple queries in sequence."""
    # Set up mock for the queries
    mock_prolog.query.side_effect = [
        [{}],  # consult success
        [{"X": "socrates"}],  # first query result
        [],  # second query result (no solutions)
    ]
    
    # Load knowledge base
    code = "human(socrates). mortal(X) :- human(X)."
    result = await prolog_server.consult(code=code)
    assert result["success"] is True
    
    # Execute queries
    result1 = await prolog_server.query(query="mortal(X)")
    result2 = await prolog_server.query(query="immortal(X)")
    
    # Verify results
    assert result1["success"] is True
    assert len(result1["solutions"]) == 1
    assert result2["success"] is True
    assert len(result2["solutions"]) == 0


@pytest.mark.asyncio
async def test_concurrent_queries(prolog_server, mock_prolog):
    """Test handling concurrent Prolog queries."""
    # Set up multiple queries
    queries = ["mortal(X)", "human(Y)", "immortal(Z)"]
    mock_prolog.query.side_effect = [
        [{"X": "socrates"}],
        [{"Y": "plato"}],
        []
    ]
    
    # Execute queries concurrently
    results = await asyncio.gather(
        *[prolog_server.query(query=q) for q in queries]
    )
    
    # Verify all queries completed
    assert len(results) == 3
    assert all(r["success"] for r in results)
    assert len(results[0]["solutions"]) == 1
    assert len(results[1]["solutions"]) == 1
    assert len(results[2]["solutions"]) == 0


@pytest.mark.asyncio
async def test_server_cleanup(mock_prolog):
    """Test proper cleanup of Prolog resources."""
    server = PrologMCPServer()
    await server.initialize()  # Initialize first
    server._prolog = mock_prolog  # Explicitly set the mock
    
    # Simulate server shutdown
    await server.cleanup()
    
    # Verify Prolog thread was cleaned up
    mock_prolog.stop.assert_called_once()


@pytest.mark.asyncio
async def test_invalid_prolog_code(prolog_server, mock_prolog):
    """Test handling of invalid Prolog code."""
    # Simulate syntax error in code
    invalid_code = "invalid_predicate(x"  # Missing closing parenthesis
    mock_prolog.query.side_effect = Exception("Syntax error")
    
    result = await prolog_server.consult(code=invalid_code)
    
    assert result["success"] is False
    assert "error" in result
    assert "syntax error" in result["error"].lower()


@pytest.mark.asyncio
async def test_query_timeout(prolog_server, mock_prolog):
    """Test handling of query timeouts."""
    # Simulate a query that takes too long
    mock_prolog.query.side_effect = Exception("Time limit exceeded")
    
    result = await prolog_server.query(query="infinite_loop")
    
    assert result["success"] is False
    assert "time limit exceeded" in result["error"].lower()
    assert result["solutions"] == []


@pytest.mark.asyncio
async def test_empty_input_handling(prolog_server):
    """Test handling of empty inputs."""
    # Test empty consult
    result = await prolog_server.consult(code="")
    assert result["success"] is False
    assert "empty code" in result["error"].lower()
    
    # Test empty query
    result = await prolog_server.query(query="")
    assert result["success"] is False
    assert "empty query" in result["error"].lower()


@pytest.mark.asyncio
async def test_cleanup_error(mock_prolog):
    """Test handling of cleanup errors."""
    server = PrologMCPServer()
    await server.initialize()  # Initialize first
    server._prolog = mock_prolog
    
    # Simulate error during stop
    mock_prolog.stop.side_effect = Exception("Cleanup failed")
    
    # Should not raise exception
    await server.cleanup()


@pytest.mark.asyncio
async def test_complex_query_handling(prolog_server, mock_prolog):
    """Test handling of complex queries with multiple solutions."""
    # Set up mock to return multiple solutions
    mock_prolog.query.return_value = [
        {"X": "socrates", "Y": "human"},
        {"X": "plato", "Y": "human"},
        {"X": "aristotle", "Y": "human"}
    ]
    
    result = await prolog_server.query(query="philosopher(X), type(X, Y)")
    
    assert result["success"] is True
    assert len(result["solutions"]) == 3
    assert all("X" in sol and "Y" in sol for sol in result["solutions"])
    assert all(sol["Y"] == "human" for sol in result["solutions"])


@pytest.mark.asyncio
async def test_unicode_handling(prolog_server, mock_prolog):
    """Test handling of Unicode characters in Prolog code and queries."""
    # Test Unicode in consult
    code = """
    person('José').
    greeting('¡Hola!').
    """
    mock_prolog.query.return_value = [{}]  # Success
    result = await prolog_server.consult(code=code)
    assert result["success"] is True
    
    # Test Unicode in query
    mock_prolog.query.return_value = [{"X": "¡Hola!"}]
    result = await prolog_server.query(query="greeting(X)")
    
    assert result["success"] is True
    assert result["solutions"][0]["X"] == "¡Hola!"


@pytest.mark.asyncio
async def test_server_context(mock_prolog):
    """Test using server within an async context manager."""
    async with PrologMCPServer() as server:
        # Configure mock after initialization
        server._prolog = mock_prolog
        server._initialized = True

        # Verify server is initialized and working
        mock_prolog.query.return_value = [{"X": "test"}]
        result = await server.query("test")
        assert result["success"] is True
        assert len(result["solutions"]) == 1
    
    # Verify cleanup was called
    mock_prolog.stop.assert_called_once()


@pytest.mark.asyncio
async def test_server_query_validation():
    """Test query validation and error handling."""
    server = PrologMCPServer()
    
    # Test uninitialized server
    with pytest.raises(AttributeError):
        await server.query("test")
    
    # Initialize server with mock
    await server.initialize()
    server._prolog = create_mock_thread()
    
    # Test invalid query types
    with pytest.raises(AttributeError):
        await server.query(None)
        
    with pytest.raises(AttributeError):
        await server.query(123)


@pytest.mark.asyncio
async def test_server_stress(prolog_server, mock_prolog):
    """Test server under stress with many concurrent queries."""
    # Prepare a large number of queries
    num_queries = 100
    queries = ["test_query"] * num_queries
    
    # Configure mock to return different results for each query
    mock_prolog.query.side_effect = [
        [{"result": f"result_{i}"}] for i in range(num_queries)
    ]
    
    # Execute all queries concurrently
    results = await asyncio.gather(
        *[prolog_server.query(query=q) for q in queries]
    )
    
    # Verify results
    assert len(results) == num_queries
    assert all(r["success"] for r in results)
    assert all(isinstance(r["solutions"], list) for r in results)