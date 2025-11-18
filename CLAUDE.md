# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

WolfAI is a multiplayer Werewolf game with AI players that use advanced reasoning techniques. It's a monorepo with a Python FastAPI backend and React TypeScript frontend.

## Development Commands

### Backend (Python)

```bash
# Setup
cd backend
pip install -e ".[dev]"

# Testing
pytest                              # Run all tests
pytest tests/e2e/                   # Run E2E tests
pytest -k "test_name"               # Run specific test
pytest -m "not slow"                # Skip slow tests

# Linting
ruff check .                        # Check code quality
ruff check --fix .                  # Auto-fix issues
pylint --rcfile=.pylintrc src/ tests/  # Check duplicate code

# From project root
npm run test:py                     # Run all tests
npm run test:e2e                    # Run E2E tests
npm run lint:py                     # Run all linters (Ruff + Pylint)
npm run lint:py:fix                 # Auto-fix linting issues
```

### Frontend (React + TypeScript)

```bash
cd frontend
npm install
npm run dev                         # Start dev server
npm run build                       # Build for production
```

### CI/CD

The CI pipeline runs on Python 3.11 and 3.12, requiring SWI-Prolog as a system dependency. All tests must pass, and code must satisfy Ruff linting before merging.

## Architecture

### 4-Layer Backend Architecture

1. **REST API & WebSocket Layer** (`api.py`)
   - FastAPI server with 7 endpoints (POST /new-game, GET /games, GET /state/{game_id}, POST /action, POST /end-game, WS /ws/{game_id})
   - In-memory game session management
   - Real-time state broadcast via WebSocket to all connected clients

2. **Game Engine State Machine** (`arena.py`)
   - Core Werewolf game logic with 6 explicit phases: INITIALIZED → NIGHT → DAY → VOTING → RESOLUTION → GAME_OVER
   - Role-based action validation (Werewolf, Villager, Seer, Doctor, etc.)
   - Information hiding: `public_view()` vs `get_player_view(player_id)` to enforce game fairness
   - All state transitions are deterministic and testable

3. **Agent & Reasoning Layer** (`agents/prolog.py`)
   - LLM to Prolog bridge via MCP (Model Context Protocol)
   - Tool discovery and async invocation with retry logic
   - **Note**: Requires migration to LangChain 1.0+ (currently using deprecated APIs)

4. **Tool Infrastructure Layer** (`tools/`)
   - `mcp_utils.py`: Converts Python type hints → JSON schemas automatically
   - `mcp_server_factory.py`: Turns any Python module into an MCP server via decorators
   - `langchain_utils.py`: Bridges MCP tools to LangChain StructuredTools
   - `tools/pl/prolog.py`: Safe, isolated Prolog execution with immutable state (frozen dataclasses)

### Key Architectural Patterns

- **State Machine**: Explicit phases prevent invalid game transitions
- **Functional Immutability**: Frozen `PrologState` dataclass for thread-safe access
- **Namespace Isolation**: Each Prolog query runs in unique namespace (`ns_<uuid>`) for isolation
- **Type-Driven Generation**: Python type hints are single source of truth for JSON schemas
- **Generic Server Factory**: Any Python module becomes MCP server with `@mcp_tool` decorator
- **Broadcast Pattern**: WebSocket clients receive consistent state updates
- **Information Visibility**: Separate public/player views maintain game integrity
- **Async/Await**: All I/O is async for scalability

### Component Interaction Flow

```
User Action → REST API → Arena State Machine → WebSocket Broadcast → All Clients
                                ↓
                        Event Processing
                    (Validate Phase, Role, etc.)
                                ↓
                        Update Game State
                    (Phase Transition, Eliminations)
                                ↓
                        Information Filtering
                    (public_view, get_player_view)
```

## Testing Strategy

### Test Organization

- `tests/` - Comprehensive test suite (71+ passing tests)
- `tests/e2e/` - End-to-end BDD tests using pytest-bdd
- `tests/agents/` - Agent behavior tests
- `tests/tools/` - Tool integration tests

### Test Configuration

- All tests use `asyncio_mode = "auto"` (configured in pyproject.toml)
- Async tests automatically detected and handled
- Custom markers: `slow`, `integration`, `gamelib`, `asyncio`, `e2e`, `bdd`
- Use `-m "not slow"` to skip slow tests during development

## Code Quality Standards

### Linting Rules

**Ruff** (primary linter):
- Line length: 100 characters
- Enabled rules: E, F, I, B, W, C90, PLR, SIM
- Max cyclomatic complexity: 10
- Max function args: 5
- Max branches: 12
- Max returns: 6
- Max statements: 50

**Pylint** (duplicate code detection):
- Detects 4+ line duplicates
- Ignores comments, docstrings, imports, signatures

### Critical Requirements

1. **Exception Chaining**: Always use `raise ... from err` to preserve tracebacks
2. **Abstract Methods**: Mark with `@abstractmethod` decorator
3. **Complexity**: Break down functions exceeding complexity limits
4. **No LRU Cache on Instance Methods**: Use module-level functions to avoid memory leaks

## Dependencies

### System Requirements

- Python 3.11 or 3.12
- SWI-Prolog (required for Prolog integration)

### Core Dependencies

- FastAPI - Web framework
- LangGraph, LangChain - Agent framework (⚠️ migration to 1.0+ needed)
- pyswip - Python-SWI-Prolog bridge
- Typer - CLI framework
- python-dotenv - Environment configuration
- mcp - Model Context Protocol

### Development Dependencies

- pytest, pytest-asyncio, pytest-bdd - Testing
- ruff, pylint - Linting
- mypy - Type checking (strict mode enabled)
- coverage - Code coverage

## Important Constraints

### API Design

- `OPENAI_API_KEY` environment variable required for agent functionality
- All API responses use Pydantic models for validation
- Game state is in-memory (no persistence yet)
- WebSocket connections must handle reconnection logic

### State Management

- Arena state is the single source of truth
- State transitions are synchronous and atomic
- All game state changes broadcast to WebSocket clients
- Player-specific information filtered before transmission

### Prolog Integration

- Each query creates isolated namespace for safety
- State is immutable (frozen dataclasses)
- All Prolog operations are deterministic and testable
- Requires SWI-Prolog 8.0+ installed system-wide

## Extending the System

### Adding New Game Roles

1. Add enum to `GamePhase` and `PlayerRole` in arena.py
2. Implement role-specific validation in `_validate_action()`
3. Add role behavior in phase processing methods
4. Update information filtering in `get_player_view()`
5. Add comprehensive tests

### Adding New MCP Tools

1. Create function with proper type hints in `tools/` module
2. Decorate with `@mcp_tool` from `mcp_server_factory.py`
3. Type hints automatically converted to JSON schema
4. Tool becomes available to all agents via MCP protocol

### Future Scaling Considerations

- Persistence: Add SQLAlchemy ORM for database
- Scaling: Introduce Redis for session state, RabbitMQ for message queue
- Observability: Add structured logging, OpenTelemetry
- Frontend: React Router already configured for multi-page navigation
