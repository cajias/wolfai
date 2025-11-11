"""FastAPI REST and WebSocket endpoints for Werewolf game."""

from __future__ import annotations

import uuid

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

from .arena import Arena


app = FastAPI()


class GameState(BaseModel):
    """Public representation of a game session."""

    state: str
    actions: list[str] = Field(default_factory=list)
    day_number: int = 0
    alive_players: list[str] = Field(default_factory=list)
    dead_players: list[str] = Field(default_factory=list)
    winner: str | None = None
    player_count: int = 0


class PlayerView(BaseModel):
    """Player-specific view with private information."""

    state: str
    actions: list[str] = Field(default_factory=list)
    day_number: int = 0
    alive_players: list[str] = Field(default_factory=list)
    dead_players: list[str] = Field(default_factory=list)
    winner: str | None = None
    player_count: int = 0
    your_role: str
    your_status: str
    investigations: list[tuple[str, str]] | None = None
    fellow_werewolves: list[str] | None = None


class GameId(BaseModel):
    """Identifier for a game session."""

    game_id: str


class PlayerConfig(BaseModel):
    """Player configuration for game creation."""

    player_id: str
    role: str


class NewGameRequest(BaseModel):
    """Request to create a new game with custom players."""

    players: list[PlayerConfig] | None = None


class Action(BaseModel):
    """Action submitted by a player."""

    game_id: str
    actor_id: str
    action: str


class Status(BaseModel):
    """Generic status response."""

    status: str
    message: str | None = None


class GameList(BaseModel):
    """Collection of active game identifiers."""

    games: list[str] = Field(default_factory=list)


class ValidActions(BaseModel):
    """Valid actions for a player."""

    actions: list[str] = Field(default_factory=list)


# In-memory store of active game sessions. Each session is backed by an
# ``Arena`` instance which maintains hidden state such as player roles.
_games: dict[str, Arena] = {}
_connections: dict[str, list[WebSocket]] = {}


async def _broadcast(game_id: str) -> None:
    """Send the current state to all connected clients."""
    arena = _games.get(game_id)
    if arena is None:
        return
    for ws in list(_connections.get(game_id, [])):
        try:
            await ws.send_json(GameState(**arena.public_view()).model_dump())
        except Exception:
            _connections[game_id].remove(ws)


@app.get("/games", response_model=GameList)
async def list_games() -> GameList:
    """Return identifiers for all active game sessions."""
    return GameList(games=list(_games.keys()))


@app.post("/new-game", response_model=GameId)
async def new_game(request: NewGameRequest | None = None) -> GameId:
    """Create a new game and return its identifier.

    If no players are specified, creates a default game with player1 (villager)
    and player2 (werewolf) for backward compatibility.
    """
    if request is None:
        request = NewGameRequest()

    game_id = str(uuid.uuid4())
    arena = Arena()

    if request.players:
        # Custom game configuration
        for player_config in request.players:
            try:
                arena.add_player(player_config.player_id, player_config.role)
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e)) from e
    else:
        # Default configuration for backward compatibility
        arena.add_player("player1", "villager")
        arena.add_player("player2", "werewolf")

    _games[game_id] = arena
    return GameId(game_id=game_id)


@app.post("/action", response_model=Status)
async def action(event: Action) -> Status:
    """Submit an action for a given game."""
    arena = _games.get(event.game_id)
    if arena is None:
        raise HTTPException(status_code=404, detail="Game not found")

    try:
        arena.apply_action(event.actor_id, event.action)
        await _broadcast(event.game_id)
        return Status(status="ok", message="Action processed successfully")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@app.get("/state/{game_id}", response_model=GameState)
async def get_state(game_id: str) -> GameState:
    """Retrieve the current state of a game."""
    arena = _games.get(game_id)
    if arena is None:
        raise HTTPException(status_code=404, detail="Game not found")
    return GameState(**arena.public_view())


@app.get("/player-view/{game_id}/{player_id}", response_model=PlayerView)
async def get_player_view(game_id: str, player_id: str) -> PlayerView:
    """Get player-specific view including their role and private information."""
    arena = _games.get(game_id)
    if arena is None:
        raise HTTPException(status_code=404, detail="Game not found")

    try:
        view = arena.get_player_view(player_id)
        return PlayerView(**view)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@app.get("/valid-actions/{game_id}/{player_id}", response_model=ValidActions)
async def get_valid_actions(game_id: str, player_id: str) -> ValidActions:
    """Get list of valid actions for a player in the current game state."""
    arena = _games.get(game_id)
    if arena is None:
        raise HTTPException(status_code=404, detail="Game not found")

    actions = arena.get_valid_actions(player_id)
    return ValidActions(actions=actions)


@app.post("/end-game", response_model=Status)
async def end_game(game_id: GameId) -> Status:
    """End a game and remove it from memory."""
    if _games.pop(game_id.game_id, None) is None:
        raise HTTPException(status_code=404, detail="Game not found")
    for ws in _connections.pop(game_id.game_id, []):
        await ws.close()
    return Status(status="ended", message="Game ended successfully")


@app.websocket("/ws/{game_id}")
async def websocket_updates(websocket: WebSocket, game_id: str) -> None:
    """Allow clients to subscribe to game state updates."""
    await websocket.accept()
    _connections.setdefault(game_id, []).append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        _connections[game_id].remove(websocket)
