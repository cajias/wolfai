"""MCP server for the Prolog module."""

import click
from .. import mcp_server_factory
from . import prolog


@click.command()
@click.option("--port", default=8000, help="Port to listen on for SSE")
@click.option(
    "--transport",
    type=click.Choice(["stdio", "sse"]),
    default="stdio",
    help="Transport type",
)
def main(port: int, transport: str) -> int:
    mcp_server_factory.run_server(
        module=prolog,
        name="prolog-mcp-server",
        port=port,
        transport=transport
    )
    return 0


if __name__ == "__main__":
    main()
