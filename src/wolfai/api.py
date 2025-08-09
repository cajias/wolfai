from __future__ import annotations

import uuid
from typing import Dict, List

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

from .arena import Arena

app = FastAPI()


class GameState(BaseModel):
    """Public representation of a game session."""

    state: str
    actions: List[str] = Field(default_factory=list)


class GameId(BaseModel):
    """Identifier for a game session."""

    game_id: str


class Action(BaseModel):
    """Action submitted by a player."""

    game_id: str
    actor_id: str
    action: str


class Status(BaseModel):
    """Generic status response."""

    status: str


class GameList(BaseModel):
    """Collection of active game identifiers."""

    games: List[str] = Field(default_factory=list)


# In-memory store of active game sessions. Each session is backed by an
# ``Arena`` instance which maintains hidden state such as player roles.
_games: Dict[str, Arena] = {}
_connections: Dict[str, List[WebSocket]] = {}


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
async def new_game() -> GameId:
    """Create a new game and return its identifier."""

    game_id = str(uuid.uuid4())
    arena = Arena()
    # Example hidden state: assign roles to two players. The roles are never
    # exposed through the API but are kept server-side for game logic.
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
    arena.apply_action(event.actor_id, event.action)
    await _broadcast(event.game_id)
    return Status(status="ok")


@app.get("/state/{game_id}", response_model=GameState)
async def get_state(game_id: str) -> GameState:
    """Retrieve the current state of a game."""

    arena = _games.get(game_id)
    if arena is None:
        raise HTTPException(status_code=404, detail="Game not found")
    return GameState(**arena.public_view())


@app.post("/end-game", response_model=Status)
async def end_game(game_id: GameId) -> Status:
    """End a game and remove it from memory."""

    if _games.pop(game_id.game_id, None) is None:
        raise HTTPException(status_code=404, detail="Game not found")
    for ws in _connections.pop(game_id.game_id, []):
        await ws.close()
    return Status(status="ended")


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
