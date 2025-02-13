"""State observation interface."""

from typing import Protocol, Dict, Set, Any, TypeVar

GameStateType = TypeVar('GameStateType')

class StateObserver(Protocol[GameStateType]):
    """Interface for observing game state."""

    def get_active_actors(self) -> Set[str]:
        """Get set of currently active actors."""
        ...

    def get_actor_state(self, actor_id: str) -> Dict[str, Any]:
        """Get the current state for a specific actor."""
        ...

    def get_public_state(self) -> Dict[str, Any]:
        """Get the publicly visible game state."""
        ...

    def get_state_view(self, actor_id: str) -> Dict[str, Any]:
        """Get the game state from a specific actor's perspective."""
        ...
