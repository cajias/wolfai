from .simple_env import SimpleEnvironment
from ...gamelib import Event, Actor


class SimpleActor(Actor):
    """Represents an agent that interacts with the environment."""

    def __init__(self, actor_id: str, env: SimpleEnvironment | None):
        self._actor_id = actor_id
        self.env = env  # ✅ Reference to the environment

    def id(self) -> str:
        """Return the actor's ID."""
        return self._actor_id

    async def receive_event(self, event: Event):
        """Process an event received from the environment."""
        print(f"Actor {self._actor_id} received event: {event}")

        # ✅ Example: If it's the actor's turn, it takes an action
        if event.type == "your_turn" and event.to_actor_id == self._actor_id:
            action = {"move": "north"}  # Example action
            await self.act("action", action)

    async def act(self, event_type: str, data: dict = None):
        """Emit an action into the environment."""

        event = Event(type=event_type, from_id=self.id(), data=data or {})
        await self.env.emit(event)  # ✅ Call emit on the environment
