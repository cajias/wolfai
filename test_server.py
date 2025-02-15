"""Test just the Prolog MCP server."""
import asyncio
from src.wolfai.tools.pl.prolog_mcp_server import create_prolog_server

async def test_server():
    print("Creating Prolog server...")
    server = await create_prolog_server()
    
    print("Server created, running test query...")
    try:
        # Get tools
        tools = server.list_tools()
        print(f"Available tools: {[t.name for t in tools]}")
        
        # Test consult
        code = """
        human(socrates).
        mortal(X) :- human(X).
        """
        
        result = await server.call_tool("consult", {"code": code})
        print(f"Consult result: {result}")
        
        # Test query
        result = await server.call_tool("query", {"query": "mortal(socrates)"})
        print(f"Query result: