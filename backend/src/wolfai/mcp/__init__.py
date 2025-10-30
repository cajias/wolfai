"""MCP (Model Context Protocol) server infrastructure.

This module provides utilities and server implementations for exposing
Python functionality via MCP servers.
"""

from .server import ModuleServer, run_server
from .utils import (
    generate_from_module,
    function_to_mcp_tool,
    function_to_mcp_prompt,
    generate_tools_from_module,
    generate_prompts_from_module,
)

__all__ = [
    # Server infrastructure
    "ModuleServer",
    "run_server",
    # Utility functions
    "generate_from_module",
    "function_to_mcp_tool",
    "function_to_mcp_prompt",
    "generate_tools_from_module",
    "generate_prompts_from_module",
]
