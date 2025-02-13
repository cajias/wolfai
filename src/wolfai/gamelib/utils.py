"""Utility functions for running games and actors."""

from typing import Optional
from .types import Event
from .game import Game
from .environment import Environment
from .actor import Actor

async def run_game(game: Game, environment: Environment):
    """Run a game system.

    Args:
        game: The game state machine
        environment: The game environment
    """
    async for event in environment.event_stream():
        if event.type == "action":
            if game.validate_action(event):
                new_state = game.transition_state()
                await environment.emit(Event(
                    type="state_changed",
                    data={"new_state": new_state}
                ))
            else:
                await environment.emit(Event(
                    type="action_invalid",
                    data={"reason": "Invalid action"},
                    actor_id=event.actor_id
                ))
