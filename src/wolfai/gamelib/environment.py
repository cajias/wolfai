"""Environment interface for managing events and actor interactions."""

from typing import Protocol, AsyncIterator, List, TypeVar
from .types import Event

GameStateType = TypeVar('GameStateType')

class Environment(Protocol[GameStateType]):
    """Interface for the game environment that manages actor interactions."""

    async def register_actor(self, actor_id: str) ->AsyncIterator[Event]:
        """Stream of all game events relevant to the actor.

        Events can be:
        - Actions from actors
        - Game state changes
        - Results of actions
        - System events
        etc.

        Usage:
            async for event in environment.event_stream():
                # Process event
        """

        ...

    async def emit(self, event: Event):
        """Emit an event into the environment.

        This is how actors and the game system communicate with the environment.
        The environment will process the event and potentially emit follow-up
        events through the event stream.
        """
        ...

    def get_event_history(self) -> List[Event]:
        """Get the full history of game events."""
        ...
