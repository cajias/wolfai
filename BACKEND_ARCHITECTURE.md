# WolfAI Backend Architecture

## Overview

The WolfAI backend is a FastAPI-based service designed to host a multiplayer Werewolf game where humans and AI agents can play together. The architecture is structured in layers with clear separation of concerns.

## Architecture Layers

```
┌─────────────────────────────────────────────────────────────┐
│                    API Layer (FastAPI)                       │
│  REST + WebSocket endpoints for game management             │
│  - /new-game, /action, /state, /end-game, /games           │
│  - WebSocket: /ws/{game_id} for real-time updates          │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                  Game State Layer                            │
│  Arena: Manages game sessions, hidden state, player roles   │
│  - Stores secret information (player roles)                 │
│  - Provides public views (visible game state)               │
│  - Applies actions and transitions game phases              │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                Game Logic Abstractions                       │
│  Protocol-based interfaces for extensibility:               │
│  - Actor: Player/AI agent interface                         │
│  - Environment: Event queue and dispatch system             │
│  - Game: State validation and transition rules              │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                   AI Agent Layer                             │
│  PrologAgent: Natural language → Prolog reasoning           │
│  (Currently requires LangChain 1.0+ migration)              │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                  Tool Integration Layer                      │
│  - Prolog Engine (SWI-Prolog via PySwip)                   │
│  - MCP (Model Context Protocol) server/client              │
│  - LangChain tool adapters                                  │
└─────────────────────────────────────────────────────────────┘
```

## Key Components

### 1. API Layer (`api.py`)

**Purpose**: HTTP/WebSocket interface for clients

**Key Features**:
- **REST Endpoints**: Create games, submit actions, query state
- **WebSocket Support**: Real-time game updates via broadcast
- **Session Management**: In-memory game storage with UUID identifiers
- **Security**: Server-side hidden state (roles never exposed to clients)

**Data Flow**:
```
Client → POST /new-game → Create Arena → Return game_id
Client → POST /action → Arena.apply_action() → Broadcast via WebSocket
Client → WS /ws/{game_id} → Subscribe to game updates
```

### 2. Arena (`arena.py`)

**Purpose**: Game state manager (currently a placeholder)

**Current State**:
- **Minimal Implementation**: Tracks roles, phase, and actions
- **Hidden State**: Player roles stored server-side only
- **Public Views**: Returns sanitized state for clients
- **Future**: Will implement full Werewolf game rules

**Key Methods**:
```python
add_player(actor_id, role)      # Register player with secret role
apply_action(actor_id, action)  # Process player action
public_view()                   # Return safe public state
```

### 3. Game Library (`gamelib/`)

**Purpose**: Protocol-based abstractions for extensible game logic

**Components**:

**Actor Protocol** (`actor.py`):
```python
class Actor(Protocol):
    async def receive_event(event)  # Process incoming events
    async def act(event_type, data)  # Emit actions
    def id() -> str                  # Unique identifier
```

**Environment Protocol** (`environment.py`):
```python
class Environment(Protocol):
    async def run()                   # Event loop
    async def emit(event)             # Add event to queue
    async def dispatch_event(event)   # Send to actors
    def get_event_history()           # Full game log
```

**Game Protocol** (`game.py`):
```python
class Game(Protocol):
    def get_valid_actions(actor_id)   # Legal moves
    def transition_state()            # Advance game phase
    def validate_action(event)        # Check if legal
    def is_terminal_state()           # Game over check
```

### 4. AI Agent Layer (`agents/`)

**PrologAgent** (`agents/prolog.py`):
- **Goal**: Convert natural language to Prolog reasoning
- **Status**: ⚠️ Requires migration to LangChain 1.0+ API
- **Current Issue**: Uses deprecated `initialize_agent`
- **Architecture**:
  ```
  User Query → LLM → Prolog Code → SWI-Prolog → Results → LLM → Response
  ```

**Key Features** (when functional):
- Natural language interface to logical reasoning
- Prolog knowledge base management
- Strategic decision-making via logic programming
- MCP server integration for tool access

### 5. Tool Integration Layer (`tools/`)

**Prolog Integration** (`tools/pl/`):
- **prolog.py**: PySwip wrapper for SWI-Prolog
- **prolog_chains.py**: LangChain prompts for NL→Prolog conversion
- **prolog_mcp_server.py**: MCP server exposing Prolog tools

**MCP (Model Context Protocol)** (`tools/mcp_*.py`):
- **mcp_utils.py**: Convert Python functions to MCP tools
- **mcp_server_factory.py**: Create MCP servers from modules
- **langchain_utils.py**: Adapt MCP tools to LangChain format

**Purpose**: Bridge between LLMs and external tools/APIs

## Data Flow Example

### Creating and Playing a Game

```
1. Client: POST /new-game
   ↓
2. API: Creates Arena instance with UUID
   - Arena.add_player("player1", "villager")
   - Arena.add_player("player2", "werewolf")
   ↓
3. API: Returns game_id to client
   ↓
4. Client: WebSocket connect to /ws/{game_id}
   ↓
5. Client: POST /action with game action
   ↓
6. API: arena.apply_action(actor_id, action)
   ↓
7. API: Broadcast updated state via WebSocket
   ↓
8. All connected clients receive GameState update
```

## Current Status

### ✅ Working
- FastAPI REST API with session management
- WebSocket real-time updates
- Arena placeholder with hidden state
- Game library protocol interfaces
- Prolog integration (when SWI-Prolog installed)
- MCP tool generation utilities

### 🚧 In Progress / Needs Work
- **Arena Implementation**: Currently just a placeholder
  - No actual Werewolf game rules
  - No state machine for game phases
  - No victory condition checking

- **PrologAgent**: Requires LangChain 1.0+ migration
  - Uses deprecated `initialize_agent` API
  - Needs migration to `create_react_agent`
  - Integration tests skipped

- **Game Logic**: Protocol interfaces defined but not implemented
  - No concrete Actor implementations
  - No Environment event queue system
  - No Game state machine

### 🎯 Intended Architecture (from README)

The full vision includes:

```
Arena → AI Agents → Multi-Agent System → Reasoning Engines
                    ├─ Prolog (logic & deduction)
                    ├─ MiniZinc (constraint optimization)
                    └─ Probability Models (Bayesian, HMM, POMDP, Kalman)
```

**AI Decision Pipeline**:
1. **Belief Update**: Process observations (accusations, votes)
2. **Logical Check**: Verify consistency with Prolog
3. **Simulation**: Model future states
4. **Optimization**: Use MiniZinc for best action
5. **Execution**: Take action in game

## Technology Stack

### Core
- **FastAPI**: Async web framework
- **Pydantic**: Data validation and serialization
- **WebSockets**: Real-time communication

### AI/ML
- **LangChain**: LLM orchestration framework
- **LangGraph**: State machine for agents
- **OpenAI**: Language model API

### Reasoning
- **SWI-Prolog** (via PySwip): Logical inference
- **MiniZinc**: (Planned) Constraint optimization
- **Probabilistic Models**: (Planned) Belief updates

### Integration
- **MCP**: Model Context Protocol for tool integration
- **Python Type Hints**: Protocol-based interfaces

## Testing Strategy

### Unit Tests
- API endpoint tests (`tests/test_api.py`)
- MCP utility tests (`tests/tools/test_mcp_*.py`)
- Prolog tests (require SWI-Prolog)

### Integration Tests
- PrologAgent tests (currently skipped - needs migration)
- WebSocket broadcast tests
- End-to-end game flow tests

### Test Infrastructure
- pytest with async support
- Automatic skipping when SWI-Prolog unavailable
- FastAPI TestClient for API testing

## Next Steps for Development

### Short Term
1. **Implement Arena game rules**:
   - State machine for Werewolf phases
   - Victory condition checking
   - Role-specific actions

2. **Migrate PrologAgent to LangChain 1.0+**:
   - Replace `initialize_agent` with `create_react_agent`
   - Update agent initialization code
   - Re-enable integration tests

3. **Implement concrete Actor**:
   - Human player actor
   - AI agent actor with belief system

### Medium Term
4. **Add MiniZinc integration**:
   - Constraint optimization for strategy
   - Action selection under uncertainty

5. **Implement Environment event system**:
   - Event queue and dispatch
   - Event history tracking

6. **Build belief update system**:
   - Bayesian inference for hidden information
   - Probability tracking per player

### Long Term
7. **Advanced AI reasoning**:
   - HMM for behavior modeling
   - POMDP for decision under uncertainty
   - Kalman filters for belief refinement

8. **Scalability**:
   - Database persistence (PostgreSQL)
   - Redis for session management
   - Horizontal scaling support

## Security Considerations

### Current Implementation
- ✅ Hidden state (roles) never exposed via API
- ✅ Server-side validation
- ✅ UUID-based session identifiers

### Needed
- ⚠️ Authentication and authorization
- ⚠️ Rate limiting
- ⚠️ Input validation and sanitization
- ⚠️ CORS configuration
- ⚠️ WebSocket authentication

## Configuration

### Environment Variables
- `OPENAI_API_KEY`: Required for LangChain/OpenAI integration

### Server Configuration
- In-memory storage (no persistence)
- No connection limits
- No rate limiting

## Deployment

### Current Setup
- Development mode only
- No production configuration
- No containerization for deployment

### CI/CD
- GitHub Actions workflow
- Python 3.11 & 3.12 testing
- Automated linting (Ruff)
- Test suite execution

---

**Last Updated**: 2025-10-30
**Status**: Early development - core API functional, game logic placeholder
