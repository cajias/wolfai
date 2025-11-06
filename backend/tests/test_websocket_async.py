"""Async WebSocket tests using TestClient with async context."""

import asyncio
import json
from typing import Any, Dict, List

import pytest
from fastapi.testclient import TestClient

from wolfai.api import app


class TestAsyncWebSocket:
    """Async WebSocket integration tests using TestClient."""

    def test_single_client_receives_websocket_updates(self):
        """Test that a single WebSocket client receives updates."""
        with TestClient(app) as client:
            # Create a game
            response = client.post("/new-game")
            assert response.status_code == 200
            game_id = response.json()["game_id"]

            # Connect WebSocket
            with client.websocket_connect(f"/ws/{game_id}") as websocket:
                # Submit an action via HTTP
                action_response = client.post(
                    "/action",
                    json={
                        "game_id": game_id,
                        "actor_id": "player1",
                        "action": "test_action",
                    },
                )
                assert action_response.status_code == 200

                # Receive WebSocket message
                data = websocket.receive_json()

                # Verify the update
                assert "state" in data
                assert "actions" in data
                assert "test_action" in data["actions"]

    def test_multiple_clients_receive_broadcast_updates(self):
        """Test that multiple WebSocket clients all receive broadcasts."""
        with TestClient(app) as client:
            # Create a game
            response = client.post("/new-game")
            assert response.status_code == 200
            game_id = response.json()["game_id"]

            # Connect multiple WebSocket clients
            with client.websocket_connect(
                f"/ws/{game_id}"
            ) as ws1, client.websocket_connect(f"/ws/{game_id}") as ws2:
                # Submit an action
                action_response = client.post(
                    "/action",
                    json={
                        "game_id": game_id,
                        "actor_id": "player1",
                        "action": "broadcast_test",
                    },
                )
                assert action_response.status_code == 200

                # Both clients should receive the update
                data1 = ws1.receive_json()
                data2 = ws2.receive_json()

                # Verify both received the same update
                assert data1 == data2
                assert "broadcast_test" in data1["actions"]

    def test_multiple_actions_trigger_multiple_updates(self):
        """Test that multiple actions result in multiple WebSocket updates."""
        with TestClient(app) as client:
            # Create a game
            response = client.post("/new-game")
            assert response.status_code == 200
            game_id = response.json()["game_id"]

            with client.websocket_connect(f"/ws/{game_id}") as websocket:
                messages: List[Dict[str, Any]] = []

                # Submit multiple actions and collect messages
                actions = ["action1", "action2", "action3"]

                for action in actions:
                    # Submit action
                    action_response = client.post(
                        "/action",
                        json={
                            "game_id": game_id,
                            "actor_id": "player1",
                            "action": action,
                        },
                    )
                    assert action_response.status_code == 200

                    # Receive update
                    data = websocket.receive_json()
                    messages.append(data)

                # Verify we got updates for all actions
                assert len(messages) == 3
                assert "action1" in messages[0]["actions"]
                assert "action2" in messages[1]["actions"]
                assert "action3" in messages[2]["actions"]

    def test_websocket_receives_game_state_updates(self):
        """Test WebSocket receives proper game state during phase transitions."""
        with TestClient(app) as client:
            # Create a game
            response = client.post("/new-game")
            assert response.status_code == 200
            game_id = response.json()["game_id"]

            with client.websocket_connect(f"/ws/{game_id}") as websocket:
                # Start the game
                action_response = client.post(
                    "/action",
                    json={
                        "game_id": game_id,
                        "actor_id": "player1",
                        "action": "start_game",
                    },
                )
                assert action_response.status_code == 200

                # Receive update
                data = websocket.receive_json()

                # Verify phase changed to night
                assert data["state"] == "night"
                assert data["day_number"] == 1
                assert "Game started - Night 1 begins" in data["actions"]
