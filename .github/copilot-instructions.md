# GitHub Copilot Repository Instructions

## Project Overview

WolfAI is a multiplayer Werewolf game with AI players that use advanced reasoning techniques. This is a monorepo with:
- **Backend**: Python FastAPI service with LangChain/LangGraph agents
- **Frontend**: React TypeScript application
- **Tools**: Custom MCP (Model Context Protocol) tool infrastructure

## Build & Run

### Backend Setup (Python 3.11 or 3.12)

```bash
cd backend
pip install -e ".[dev]"
```

### Backend Commands

```bash
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

### Frontend Setup

```bash
cd frontend
npm install
npm run dev                         # Start dev server
npm run build                       # Build for production
```

### System Dependencies

- **SWI-Prolog 8.0+**: Required for Prolog integration (installed system-wide)
- **Python 3.11 or 3.12**: Backend runtime
- **Node.js**: Frontend development

## Architecture

### 4-Layer Backend Architecture

1. **REST API & WebSocket Layer** (`api.py`)
   - FastAPI server with 7 endpoints
   - In-memory game session management
   - Real-time state broadcast via WebSocket

2. **Game Engine State Machine** (`arena.py`)
   - 6 explicit phases: INITIALIZED → NIGHT → DAY → VOTING → RESOLUTION → GAME_OVER
   - Role-based action validation (Werewolf, Villager, Seer, Doctor, etc.)
   - Information hiding via `public_view()` vs `get_player_view(player_id)`

3. **Agent & Reasoning Layer** (`agents/prolog.py`)
   - LLM to Prolog bridge via MCP
   - Tool discovery and async invocation with retry logic
   - **Note**: Requires migration to LangChain 1.0+ (currently using deprecated APIs)

4. **Tool Infrastructure Layer** (`tools/`)
   - Type-driven JSON schema generation
   - Generic MCP server factory with decorators
   - Safe, isolated Prolog execution with immutable state

### Key Architectural Patterns

- **State Machine**: Explicit phases prevent invalid game transitions
- **Functional Immutability**: Frozen dataclasses for thread-safe access
- **Namespace Isolation**: Each Prolog query runs in unique namespace for safety
- **Type-Driven Generation**: Python type hints → JSON schemas automatically
- **Broadcast Pattern**: WebSocket clients receive consistent state updates
- **Async/Await**: All I/O is async for scalability

## Code Quality Standards

### Linting Rules (Ruff)

- Line length: 100 characters
- Enabled rules: E, F, I, B, W, C90, PLR, SIM
- Max cyclomatic complexity: 10
- Max function args: 5
- Max branches: 12
- Max returns: 6
- Max statements: 50

### Pylint (Duplicate Code Detection)

- Detects 4+ line duplicates
- Ignores comments, docstrings, imports, signatures

### Critical Requirements

1. **Exception Chaining**: Always use `raise ... from err` to preserve tracebacks
2. **Abstract Methods**: Mark with `@abstractmethod` decorator
3. **Complexity**: Break down functions exceeding complexity limits
4. **No LRU Cache on Instance Methods**: Use module-level functions to avoid memory leaks

### Type Checking

- mypy in strict mode enabled
- All code must have proper type hints

## Testing Standards

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

### Testing Requirements

- All new features require tests
- Tests must be comprehensive and cover edge cases
- Maintain or improve code coverage
- E2E tests for critical user flows

## Contribution Guidelines

### Pull Request Requirements

- All tests must pass (pytest)
- Code must satisfy Ruff linting rules
- No duplicate code (checked by Pylint)
- Type hints required for all functions
- Update documentation for significant changes

### CI/CD Pipeline

- Runs on Python 3.11 and 3.12
- Requires SWI-Prolog as system dependency
- All tests must pass before merging
- Linting checks must pass

### Code Style

- Follow existing code patterns
- Use descriptive variable names
- Add docstrings for public APIs
- Keep functions small and focused
- Prefer composition over inheritance

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

## Security Considerations

- Never commit API keys or secrets
- Validate all user inputs
- Filter sensitive game information based on player role
- Use exception chaining for proper error handling
- Follow principle of least privilege

## Dependencies

### Core Dependencies

- FastAPI - Web framework
- LangGraph, LangChain - Agent framework
- pyswip - Python-SWI-Prolog bridge
- Typer - CLI framework
- python-dotenv - Environment configuration
- mcp - Model Context Protocol

### Development Dependencies

- pytest, pytest-asyncio, pytest-bdd - Testing
- ruff, pylint - Linting
- mypy - Type checking
- coverage - Code coverage

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

## Example Task

"Add a new game role 'Guardian' that can protect one player each night from elimination. The Guardian cannot protect the same player two nights in a row. Include role validation, phase processing, state updates, information filtering, and comprehensive tests including edge cases for consecutive protection attempts."

## Additional Resources

- [README.rst](./README.rst) - Full project documentation
- [GOAL.md](./GOAL.md) - Project goals and vision
- [PLAN.md](./PLAN.md) - Development plan and milestones
- [Backend README](./backend/README.md) - Backend-specific documentation
- [Backend TESTING.md](./backend/TESTING.md) - Testing documentation
