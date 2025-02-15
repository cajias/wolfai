"""MCP server for the Prolog module with integrated prompts."""
import click

from . import prolog
from .. import mcp_server_factory


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
    mcp_server_factory.run_server(
        port=port,
        transport=transport,
        module=prolog,
        name="prolog-mcp-server"
    )

    return 0


if __name__ == "__main__":
    main()
