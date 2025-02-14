"""MCP server for the Prolog module with integrated prompts."""

import click
from mcp.server import Server
from .. import mcp_server_factory
from . import prolog
from .prolog_chains import (
    create_prolog_chain_prompt,
    create_converter_prompt,
    create_interpreter_prompt
)


@click.command()
@click.option("--port", default=8000, help="Port to listen on for SSE")
@click.option(
    "--transport",
    type=click.Choice(["stdio", "sse"]),
    default="stdio",
    help="Transport type",
)
def main(port: int, transport: str) -> int:
    """Run the Prolog MCP server with both tools and prompts."""
    app = mcp_server_factory.create_server(
        module=prolog,
        name="prolog-mcp-server"
    )

    # Create our server instance
    server = app.create_server()

    # Register our prompts
    prompts = [
        create_prolog_chain_prompt(),
        create_converter_prompt(),
        create_interpreter_prompt()
    ]

    @server.list_prompts()
    async def list_prompts():
        return prompts

    @server.get_prompt()
    async def get_prompt(name: str, arguments=None):
        # Find the matching prompt
        prompt = next((p for p in prompts if p.name == name), None)
        if not prompt:
            raise ValueError(f"Prompt not found: {name}")

        # Return the prompt with arguments filled in
        return prompt, arguments

    # Run the server with the configured transport
    if transport == "sse":
        from mcp.server.sse import SseServerTransport
        from starlette.applications import Starlette
        from starlette.routing import Mount, Route

        sse = SseServerTransport("/messages/")

        async def handle_sse(request):
            async with sse.connect_sse(
                request.scope, request.receive, request._send
            ) as streams:
                await server.run(
                    streams[0], streams[1], server.create_initialization_options()
                )

        starlette_app = Starlette(
            debug=True,
            routes=[
                Route("/sse", endpoint=handle_sse),
                Mount("/messages/", app=sse.handle_post_message),
            ],
        )

        import uvicorn
        uvicorn.run(starlette_app, host="0.0.0.0", port=port)
    else:
        from mcp.server.stdio import stdio_server
        import anyio

        async def arun():
            async with stdio_server() as streams:
                await server.run(
                    streams[0], streams[1], server.create_initialization_options()
                )

        anyio.run(arun)

    return 0


if __name__ == "__main__":
    main()
