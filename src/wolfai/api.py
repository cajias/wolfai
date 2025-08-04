from __future__ import annotations

import uuid
from typing import Dict, List

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI()


class GameState(BaseModel):
    """Simple in-memory representation of game state."""

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


_games: Dict[str, GameState] = {}


@app.post("/new-game", response_model=GameId)
async def new_game() -> GameId:
    """Create a new game and return its identifier."""

    game_id = str(uuid.uuid4())
    _games[game_id] = GameState(state="initialized")
    return GameId(game_id=game_id)


@app.post("/action", response_model=Status)
async def action(event: Action) -> Status:
    """Submit an action for a given game."""

    game = _games.get(event.game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")
    game.actions.append(event.action)
    game.state = "updated"
    return Status(status="ok")


@app.get("/state/{game_id}", response_model=GameState)
async def get_state(game_id: str) -> GameState:
    """Retrieve the current state of a game."""

    game = _games.get(game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")
    return game


@app.post("/end-game", response_model=Status)
async def end_game(game_id: GameId) -> Status:
    """End a game and remove it from memory."""

    if _games.pop(game_id.game_id, None) is None:
        raise HTTPException(status_code=404, detail="Game not found")
    return Status(status="ended")
