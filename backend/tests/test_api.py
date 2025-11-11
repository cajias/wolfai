from fastapi.testclient import TestClient

from wolfai.api import _games, app


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


def test_websocket_updates() -> None:
    client = TestClient(app)

    game_id = client.post("/new-game").json()["game_id"]

    with client.websocket_connect(f"/ws/{game_id}") as websocket:
        client.post(
            "/action",
            json={"game_id": game_id, "actor_id": "p1", "action": "ping"},
        )
        data = websocket.receive_json()
        assert data["actions"] == ["ping"]


def test_websocket_broadcasts_to_all_clients() -> None:
    client = TestClient(app)

    game_id = client.post("/new-game").json()["game_id"]

    with client.websocket_connect(f"/ws/{game_id}") as ws1, client.websocket_connect(
        f"/ws/{game_id}",
    ) as ws2:
        client.post(
            "/action",
            json={"game_id": game_id, "actor_id": "p1", "action": "pong"},
        )
        assert ws1.receive_json()["actions"] == ["pong"]
        assert ws2.receive_json()["actions"] == ["pong"]


def test_hidden_state_not_exposed() -> None:
    """Ensure that secret server-side data stays hidden from clients."""
    client = TestClient(app)

    game_id = client.post("/new-game").json()["game_id"]

    # The arena stores hidden roles for players
    assert _games[game_id].roles

    # Public state should not leak the roles
    response = client.get(f"/state/{game_id}")
    assert response.status_code == 200
    assert "roles" not in response.json()


def test_list_games_endpoint() -> None:
    """Games endpoint returns active game identifiers."""
    client = TestClient(app)

    _games.clear()
    assert client.get("/games").json()["games"] == []

    game_id = client.post("/new-game").json()["game_id"]
    assert client.get("/games").json()["games"] == [game_id]

    client.post("/end-game", json={"game_id": game_id})
    assert client.get("/games").json()["games"] == []
