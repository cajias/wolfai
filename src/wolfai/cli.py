"""Console script for wolfai."""
import asyncio

import typer
from rich.console import Console

from src.wolfai.gamelib import Event
from src.wolfai.runtimes.simple import SimpleActor, SimpleEnvironment

app = typer.Typer()
console = Console()


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
    env_task = asyncio.create_task(env.run())

    # Emit an event that will trigger actors to act
    await env.emit(Event(type="your_turn", to_actor_id="player1", data={}))

    # Let the system run for a bit
    await asyncio.sleep(1)

    # Stop the environment
    env.stop()
    await asyncio.sleep(0.1)  # Allow graceful shutdown

    print("Event History:", env.get_event_history())


@app.command()
def main():
    """Console script for wolfai."""
    console.print("Replace this message by putting your code into "
                  "wolfai.cli.main")
    console.print("See Typer documentation at https://typer.tiangolo.com/")
    asyncio.run(run_game())


if __name__ == "__main__":
    app()
