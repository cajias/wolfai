"""Game state management interface."""

from typing import Protocol, Set, TypeVar

from .types import Event

GameStateType = TypeVar('GameStateType')
ActionType = TypeVar('ActionType')

class Game(Protocol[GameStateType, ActionType]):
    """Generic interface for game state management."""

    def get_valid_actions(self, actor_id: str) -> Set[ActionType]:
        """Return set of valid actions for the given actor in current state."""
        ...

    def transition_state(self) -> GameStateType:
        """Progress the game to the next state."""
        ...

    def get_current_state(self) -> GameStateType:
        """Get the current game state."""
        ...

    def is_terminal_state(self) -> bool:
        """Check if the current state is terminal (game ended)."""
        ...

    def validate_action(self, event: Event) -> bool:
        """Validate if an action event is legal in the current state."""
        ...
