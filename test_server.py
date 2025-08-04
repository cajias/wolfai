"""Test just the Prolog MCP server."""
import asyncio
from src.wolfai.tools.pl.prolog_mcp_server import create_prolog_server

async def test_server():
    print("Creating Prolog server...")
    server = await create_prolog_server()

    try:
        print("Server created, running test query...")
        tools = server.list_tools()
        print(f"Available tools: {[t.name for t in tools]}")

        code = """
        human(socrates).
        mortal(X) :- human(X).
        """

        result = await server.call_tool("consult", {"code": code})
        print(f"Consult result: {result}")

        result = await server.call_tool("query", {"query": "mortal(socrates)"})
        print(f"Query result: {result}")
    finally:
        await server.close()

if __name__ == "__main__":
    asyncio.run(test_server())
