"""MCP server for the Prolog module with integrated prompts."""

import click

from wolfai.tools import mcp_server_factory

from . import prolog


def main():
    """Run the Prolog MCP server."""
    @click.command()
    @click.option("--port", default=8000, help="Port to listen on for SSE")
    @click.option(
        "--transport",
        type=click.Choice(["stdio", "sse"]),
        default="stdio",
        help="Transport type",
    )
    def cli(port: int, transport: str):
        mcp_server_factory.run_server(module=prolog, port=port, transport=transport)

    cli()


if __name__ == "__main__":
    main()
