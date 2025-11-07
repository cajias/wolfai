Feature: Role-Based Gameplay
  As a werewolf game
  I want to manage player roles and game phases
  So that the game follows werewolf rules

  Background:
    Given the API server is running
    And I create a new game

  Scenario: Players have hidden roles
    When I get the game state
    Then the response should not expose player roles
    And the state should only contain public information
    But the server should maintain "player1" as "villager" internally
    And the server should maintain "player2" as "werewolf" internally

  Scenario: Game phases transition correctly
    Given the game phase is "initialized"
    When I submit action "start_game" by player "player1"
    Then the game phase should be "night"
    When I get the game state
    Then the phase should be "night"

  Scenario: Actions don't reveal actor identity
    When I submit action "test_action" by player "player1"
    And I get the game state
    Then the actions list should contain "test_action"
    But the actions list should not reveal which player acted

  Scenario: Multiple players with different roles
    # Default game has player1=villager, player2=werewolf
    When I submit action "start_game" by player "player1"
    And I submit action "advance_phase" by player "player1"
    And I submit action "player1_speaks" by player "player1"
    And I submit action "player2_speaks" by player "player2"
    Then both actions should be recorded
    And roles should remain hidden in the public view

  Scenario: Complex multi-phase game scenario
    Given the game is in "initialized" phase
    When I simulate a complete game day with the following actions:
      | actor_id | action                | expected_phase |
      | player1  | start_game            | night          |
      | player2  | advance_phase         | day            |
      | player1  | advance_phase         | voting         |
      | player2  | advance_phase         | resolution     |
      | player1  | advance_phase         | night          |
    Then all actions should be recorded in order
    And the game should maintain state consistency
    And roles should never be exposed through the API
