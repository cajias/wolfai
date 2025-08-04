from fastapi.testclient import TestClient

from src.wolfai.api import app


def test_game_flow() -> None:
    client = TestClient(app)

    # Start new game
    response = client.post("/new-game")
    assert response.status_code == 200
    game_id = response.json()["game_id"]

    # Send an action
    response = client.post(
        "/action",
        json={"game_id": game_id, "actor_id": "player1", "action": "test"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

    # Retrieve state
    response = client.get(f"/state/{game_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["actions"] == ["test"]

    # End game
    response = client.post("/end-game", json={"game_id": game_id})
    assert response.status_code == 200
    assert response.json()["status"] == "ended"

    # Game should no longer exist
    response = client.get(f"/state/{game_id}")
    assert response.status_code == 404
