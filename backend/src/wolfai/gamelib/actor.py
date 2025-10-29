"""Actor interface for game participants."""

from typing import Protocol

from src.wolfai.gamelib import Event


class Actor(Protocol):
    """Interface for game actors."""

    async def receive_event(self, event: Event):
        """Process an event received from the environment."""
        ...

    async def act(self, event_type: str, data: dict = None):
        """Emit an action into the environment."""
        ...

    def id(self) -> str:
        """Get the actor's unique identifier."""
        ...
