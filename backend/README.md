# WolfAI Backend

Python FastAPI backend service for the Werewolf AI game.

## Structure

```
backend/
├── src/wolfai/         # Python source code
│   ├── api.py         # FastAPI application
│   ├── arena.py       # Game state management
│   ├── agents/        # AI agent implementations
│   ├── tools/         # Tool integrations (Prolog, MCP)
│   ├── gamelib/       # Game logic components
│   └── runtimes/      # Runtime implementations
├── tests/             # Test suite
├── examples/          # Usage examples
└── pyproject.toml     # Python project configuration
```

## Development

### Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements_dev.txt

# Install package in editable mode
pip install -e ".[dev]"
```

### Running Tests

```bash
pytest
```

### Linting

```bash
ruff check .
```

### Building

```bash
python -m build
```

## API

The backend provides a FastAPI REST API with WebSocket support for real-time game updates.

### Endpoints

- `POST /new-game` - Create a new game session
- `GET /games` - List active game sessions
- `GET /state/{game_id}` - Get current game state
- `POST /action` - Submit a player action
- `POST /end-game` - End a game session
- `WS /ws/{game_id}` - WebSocket for real-time updates
