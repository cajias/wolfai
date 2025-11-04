"""Base types used throughout the game framework."""

import asyncio
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class Event:
    """Represents any game event - both actions and system events."""
    type: str
    data: Dict[str, Any]
    from_id: str = "environment"
    to_actor_id: str | None = None  # None for system events
    timestamp: float | None = None
    _id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = asyncio.get_event_loop().time()

    @property
    def id(self) -> str:
        """Return the ID as a constant value."""
        return self._id  # Read-only access
