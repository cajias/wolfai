from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class Arena:
    """Very small placeholder for game logic.

    The arena keeps track of secret player roles and a list of public actions.
    The secret data is intentionally not exposed through the API. This module
    acts as the server-side state manager that would normally contain the full
    game rules and logic.
    """

    roles: Dict[str, str] = field(default_factory=dict)
    phase: str = "initialized"
    actions: List[str] = field(default_factory=list)

    def add_player(self, actor_id: str, role: str) -> None:
        """Register a player with a hidden role."""
        self.roles[actor_id] = role

    def apply_action(self, actor_id: str, action: str) -> None:
        """Record an action and advance the phase.

        The actor identifier is not included in the public action list to avoid
        revealing information that might be secret, such as which player acted
        during the night phase.
        """
        self.actions.append(action)
        self.phase = "updated"

    def public_view(self) -> Dict[str, List[str]]:
        """Return data safe for public consumption."""
        return {"state": self.phase, "actions": self.actions}
