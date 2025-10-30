# MCP (Model Context Protocol) Module

This module provides infrastructure for creating and managing MCP servers that expose Python functionality to language models and AI agents.

## Architecture

```
mcp/
├── __init__.py           # Public API exports
├── server.py             # Generic MCP server factory (ModuleServer, run_server)
├── utils.py              # Utilities for generating tools/prompts from Python code
├── servers/              # Specific MCP server implementations
│   ├── __init__.py
│   └── prolog_server.py  # Prolog MCP server
└── README.md             # This file
```

## Purpose

The MCP module decouples tool functionality from agent implementations:

- **Tools** (`wolfai.tools.*`): Contain the actual implementation logic (Prolog, etc.)
- **MCP Servers** (`wolfai.mcp.servers.*`): Expose tools via Model Context Protocol
- **Agents** (`wolfai.agents.*`): Use MCP servers for tool access

This separation provides:
- **Reusability**: MCP servers can be used by multiple agents or external clients
- **Testability**: Each component can be tested independently
- **Flexibility**: Easy to swap implementations without changing agents

## Components

### 1. Server Infrastructure (`server.py`)

**ModuleServer**: Generic MCP server that exposes any Python module's functions as tools.

```python
from wolfai.mcp import ModuleServer

# Create server from any module
server = ModuleServer(my_module, name="my-server")
app = server.create_server()
```

**run_server()**: Convenience function to run an MCP server with transport (stdio or SSE).

```python
from wolfai.mcp import run_server
from wolfai.tools.pl import prolog

# Run Prolog MCP server
run_server(module=prolog, name="prolog-server", transport="stdio")
```

### 2. Utilities (`utils.py`)

Functions for introspecting Python code and generating MCP tool/prompt definitions:

- `function_to_mcp_tool()`: Convert Python function to MCP Tool
- `function_to_mcp_prompt()`: Convert Python function to MCP Prompt
- `generate_tools_from_module()`: Generate all tools from a module
- `generate_prompts_from_module()`: Generate all prompts from a module
- `generate_from_module()`: Generate both tools and prompts

These utilities use:
- Function docstrings for descriptions
- Type hints for parameter schemas
- Decorators (`@tool`, `@prompt`) for MCP metadata

### 3. Server Implementations (`servers/`)

Specific MCP server implementations for different tool sets:

**Prolog Server** (`servers/prolog_server.py`):
- Exposes Prolog reasoning capabilities via MCP
- Can be run as standalone server: `python -m wolfai.mcp.servers.prolog_server`
- Used by PrologAgent for natural language → Prolog conversion

## Usage Examples

### Creating a Custom MCP Server

```python
# 1. Define your tool module
# tools/my_tools.py
from wolfai.mcp.utils import tool

@tool
def calculate(x: int, y: int) -> int:
    """Add two numbers."""
    return x + y

# 2. Create MCP server
from wolfai.mcp import run_server
from wolfai.tools import my_tools

run_server(module=my_tools, name="calculator", transport="stdio")
```

### Using MCP Server from Agent

```python
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from mcp import StdioServerParameters
from wolfai.tools.langchain_utils import get_mcp_tools_as_langchain

# 1. Start MCP server (separate process)
server_params = StdioServerParameters(
    command="python",
    args=["-m", "wolfai.mcp.servers.prolog_server"]
)

# 2. Connect agent to server
async with stdio_client(server_params) as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize()

        # Get tools from MCP server
        tools = await get_mcp_tools_as_langchain(session)

        # Create agent with tools
        agent = create_react_agent(
            model=ChatOpenAI(),
            tools=tools
        )
```

## Session Management

MCP servers support stateful sessions:

```python
from wolfai.mcp.utils import tool

@tool
def increment(state: dict = None) -> tuple:
    """Increment counter (maintains state)."""
    if state is None:
        state = {"count": 0}

    state["count"] += 1

    # Return (result, new_state) tuple
    return state["count"], state
```

The ModuleServer automatically handles:
- Session ID management
- State storage per session
- State injection into function calls
- State updates from function returns

## Transport Options

### stdio (Standard I/O)
- Default transport
- Suitable for subprocess communication
- Used by agents connecting to server

```python
run_server(module=prolog, transport="stdio")
```

### SSE (Server-Sent Events)
- HTTP-based transport
- Suitable for web clients
- Requires port specification

```python
run_server(module=prolog, transport="sse", port=8000)
```

## Testing

Tests for MCP functionality are in `tests/mcp/`:

```bash
# Run MCP tests
pytest tests/mcp/

# Test utilities
pytest tests/mcp/test_utils.py

# Test prompts
pytest tests/mcp/test_prompts.py
```

## Development

### Adding a New MCP Server

1. Create server file in `servers/`:
```python
# servers/my_server.py
import click
from wolfai.mcp import server as mcp_server
from wolfai.tools import my_module

def main():
    @click.command()
    @click.option("--port", default=8000)
    @click.option("--transport", default="stdio")
    def cli(port, transport):
        mcp_server.run_server(
            module=my_module,
            port=port,
            transport=transport
        )
    cli()
```

2. Export in `servers/__init__.py`:
```python
from .my_server import main as my_server_main
__all__ = ["my_server_main"]
```

3. Add CLI entry point (optional):
```toml
[project.scripts]
wolfai-my-server = "wolfai.mcp.servers.my_server:main"
```

## Architecture Benefits

### Before (Coupled)
```
Agent → Direct Prolog calls
```
- Agent tightly coupled to Prolog implementation
- Hard to test agent without Prolog
- Hard to reuse Prolog functionality

### After (Decoupled)
```
Agent → MCP Client → MCP Server → Prolog Tools
```
- Agent only knows about MCP protocol
- Can mock MCP server for testing
- Prolog can be used by multiple agents/clients
- Easy to add new tools without changing agents

## Related Modules

- **`wolfai.tools.*`**: Tool implementations (Prolog, etc.)
- **`wolfai.agents.*`**: AI agents that use MCP tools
- **`wolfai.tools.langchain_utils`**: Adapters for LangChain integration

## References

- [Model Context Protocol Spec](https://modelcontextprotocol.io/)
- [LangChain Tool Calling](https://python.langchain.com/docs/how_to/tool_calling/)
- [LangGraph ReAct Agents](https://langchain-ai.github.io/langgraph/how-tos/react-agent-from-scratch/)
