Feature: Concurrent Game Sessions
  As a game platform
  I want to support multiple simultaneous games
  So that many players can play at the same time

  Background:
    Given the API server is running
    And no games are currently active

  Scenario: Create and manage multiple games simultaneously
    When I create 5 new games
    Then all 5 games should be created successfully
    And the games list should contain 5 games
    And each game should have a unique identifier

  Scenario: Actions in one game don't affect other games
    Given I create 3 new games named:
      | game_name |
      | game_a    |
      | game_b    |
      | game_c    |
    When I submit action "action_a" by player "player1" in game "game_a"
    And I submit action "action_b" by player "player2" in game "game_b"
    And I submit action "action_c" by player "player1" in game "game_c"
    Then game "game_a" should only contain action "action_a"
    And game "game_b" should only contain action "action_b"
    And game "game_c" should only contain action "action_c"

  Scenario: End one game while others continue
    Given I create 3 new games
    And I submit action "test" by player "player1" in each game
    When I end the first game
    Then the games list should contain 2 games
    And the remaining games should still be accessible
    And the remaining games should retain their actions

  Scenario: Heavy concurrent load
    When I create 10 games simultaneously
    And I submit 5 actions to each game concurrently
    Then all games should have exactly 5 actions
    And no actions should be lost or duplicated
