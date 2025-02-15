"""MCP server for the Prolog module with integrated prompts."""
import logging
import sys

import click

from wolfai.tools.mcp_server_factory import run_server
from wolfai.tools.pl import prolog

# Set up logging with more detail
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)


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
        logger.info(f"CLI starting with transport={transport}, port={port}")
        run_server(module=prolog, port=port, transport=transport)

    cli()


if __name__ == "__main__":
    main()
