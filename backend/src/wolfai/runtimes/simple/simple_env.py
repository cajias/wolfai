import asyncio
from typing import List

from src.wolfai.runtimes.simple import SimpleActor

from ...gamelib import Actor, Environment, Event


class SimpleEnvironment(Environment):
    """Simple environment for testing purposes."""

    def __init__(self, actors: List[Actor]):
        self.event_history: List[Event] = []  # Stores all past events
        self._actors = {actor.id(): actor for actor in actors}  # Actor lookup
        self._queue = asyncio.Queue()  # Async queue for event processing
        self._running = False

    async def run(self):
        """Continuously process events from the queue and dispatch them."""
        self._running = True
        while self._running:
            event = await self._queue.get()  # Wait for the next event
            self.event_history.append(event)  # Store event history
            await self.dispatch_event(event)
            self._queue.task_done()

    async def emit(self, event: Event):
        """Emit an event into the environment."""
        await self._queue.put(event)  # Add event to queue

    async def dispatch_event(self, event: Event):
        """Dispatch events to relevant actors."""
        if event.to_actor_id and event.to_actor_id in self._actors:
            # Send to a specific actor
            await self._actors[event.to_actor_id].receive_event(event)
            return

        if not event.to_actor_id:
            # Broadcast to all actors
            for actor in filter(lambda a: a.id() != event.from_id, self._actors.values()):
                await actor.receive_event(event)
            return

        # Broadcast to all actors
        for actor in self._actors.values():
            await actor.receive_event(event)

    def get_event_history(self):
        """Get the full history of game events."""
        return self.event_history

    def stop(self):
        """Stop the environment's event loop."""
        self._running = False


async def run_game():
    actors = [
        SimpleActor("player1", env=None),  # Placeholder env
        SimpleActor("player2", env=None),
    ]
    env = SimpleEnvironment(actors)

    # Assign the environment to each actor
    for actor in actors:
        actor.env = env  # ✅ Now actors can call `env.emit()`

    # Start the environment event loop
    asyncio.create_task(env.run())

    # Emit an event that will trigger actors to act
    await env.emit(Event(type="your_turn", to_actor_id="player1", data={}))

    # Let the system run for a bit
    await asyncio.sleep(1)

    # Stop the environment
    env.stop()
    await asyncio.sleep(0.1)  # Allow graceful shutdown

    print("Event History:", env.get_event_history())


if __name__ == "__main__":
    asyncio.run(run_game())
