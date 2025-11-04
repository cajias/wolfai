"""Environment interface for managing events and actor interactions."""

from typing import List, Protocol, TypeVar

from .types import Event

GameStateType = TypeVar('GameStateType')


class Environment(Protocol[GameStateType]):
    """Interface for the game environment that manages actor interactions."""

    async def run(self):
        """Continuously process events from the queue and dispatch them."""
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

    async def dispatch_event(self, event: Event):
        """Dispatch events to relevant actors."""
        ...
