"""Actor interface for game participants."""

from typing import Protocol, AsyncIterator, Callable, Awaitable
from .types import Event

class Actor(Protocol):
    """Interface for game actors."""

    async def run(self,
                 emit: Callable[[Event], Awaitable[None]],
                 events: AsyncIterator[Event]):
        """Run this actor.

        Args:
            emit: Function to emit events to the environment
            events: Stream of game events to process

        The actor will listen to the event stream and emit events
        when appropriate based on its internal logic.
        """
        ...

    @property
    def id(self) -> str:
        """Get the unique identifier for this actor."""
        ...
