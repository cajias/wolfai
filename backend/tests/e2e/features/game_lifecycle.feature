Feature: Complete Game Lifecycle
  As a game administrator
  I want to manage the full lifecycle of a werewolf game
  So that players can have a complete gaming experience

  Background:
    Given the API server is running
    And no games are currently active

  Scenario: Create and complete a basic game
    When I create a new game
    Then the game should be created successfully
    And the game should appear in the active games list
    When I get the game state
    Then the game phase should be "initialized"
    And the actions list should be empty
    When I submit action "player1 speaks" by player "player1"
    Then the action should be recorded successfully
    And the game phase should be "updated"
    And the actions list should contain "player1 speaks"
    When I end the game
    Then the game should be ended successfully
    And the game should not appear in the active games list

  Scenario: Complete multi-turn game with multiple actions
    Given I create a new game
    When I submit the following actions:
      | actor_id | action             |
      | player1  | votes for player2  |
      | player2  | defends themselves |
      | player1  | accuses player2    |
      | player2  | reveals evidence   |
    Then all actions should be recorded in order
    And the game phase should be "updated"
    When I get the game state
    Then the actions list should contain all submitted actions

  Scenario: End game cleans up resources
    Given I create a new game
    And I submit action "test action" by player "player1"
    When I end the game
    And I try to get the game state
    Then I should receive a 404 error
    When I try to submit action "another action" by player "player1"
    Then I should receive a 404 error
