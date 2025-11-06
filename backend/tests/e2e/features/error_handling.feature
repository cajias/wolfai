Feature: Error Handling and Edge Cases
  As a robust game platform
  I want to handle errors and edge cases gracefully
  So that the system remains stable under unexpected conditions

  Background:
    Given the API server is running

  Scenario: Access non-existent game
    When I try to get the state of a non-existent game
    Then I should receive a 404 error
    And the error message should be "Game not found"

  Scenario: Submit action to non-existent game
    When I try to submit action "test" by player "player1" to a non-existent game
    Then I should receive a 404 error
    And the error message should be "Game not found"

  Scenario: End non-existent game
    When I try to end a non-existent game
    Then I should receive a 404 error
    And the error message should be "Game not found"

  Scenario: Double-end game protection
    Given I create a new game
    When I end the game
    And I try to end the same game again
    Then I should receive a 404 error

  Scenario: WebSocket connection to non-existent game
    When I try to connect to WebSocket for a non-existent game
    Then the WebSocket connection should be accepted
    But no updates should be received

  Scenario: Handle invalid action data
    Given I create a new game
    When I submit an action with empty action string
    Then the action should still be recorded
    And the game should remain in a valid state

  Scenario: Rapid sequential actions
    Given I create a new game
    When I submit 50 actions rapidly from the same player
    Then all 50 actions should be recorded
    And the actions should be in the correct order

  Scenario: Games list remains consistent
    Given I create 5 new games
    When I end 3 games randomly
    Then the games list should contain exactly 2 games
    And all listed games should be accessible
