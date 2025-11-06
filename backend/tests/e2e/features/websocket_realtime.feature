Feature: WebSocket Real-Time Updates
  As a player
  I want to receive real-time game updates via WebSocket
  So that I can see game changes as they happen

  Background:
    Given the API server is running
    And I create a new game

  Scenario: Single client receives WebSocket updates
    Given I connect to the game WebSocket
    When I submit action "player1 votes" by player "player1"
    Then I should receive a WebSocket update within 2 seconds
    And the WebSocket message should contain the updated game state
    And the WebSocket message should include "player1 votes" in actions

  Scenario: Multiple clients receive broadcast updates
    Given I connect 3 clients to the game WebSocket
    When I submit action "night falls" by player "player1"
    Then all 3 clients should receive the update
    And each client should receive identical state information
    And the update should be received within 2 seconds

  Scenario: New client receives current state on connection
    Given I submit action "initial action" by player "player1"
    When I connect to the game WebSocket
    And I submit action "second action" by player "player2"
    Then I should receive the update for "second action"

  Scenario: Client handles disconnection gracefully
    Given I connect to the game WebSocket
    When I disconnect from the WebSocket
    And I submit action "test action" by player "player1"
    Then the action should still be recorded
    And no errors should be logged

  Scenario: Multiple actions trigger multiple updates
    Given I connect to the game WebSocket
    When I submit the following actions rapidly:
      | actor_id | action    |
      | player1  | action_1  |
      | player2  | action_2  |
      | player1  | action_3  |
    Then I should receive 3 WebSocket updates
    And each update should reflect the cumulative state

  Scenario: WebSocket connections closed when game ends
    Given I connect 2 clients to the game WebSocket
    When I end the game
    Then both WebSocket connections should be closed
    And clients should receive a close notification
