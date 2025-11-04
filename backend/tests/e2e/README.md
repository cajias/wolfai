# End-to-End BDD Tests for WolfAI Game

This directory contains Cucumber-style BDD (Behavior-Driven Development) tests using pytest-bdd for the WolfAI werewolf game backend.

## Overview

The e2e tests cover comprehensive game scenarios including:

- **Game Lifecycle**: Complete game creation, gameplay, and termination flows
- **Concurrent Games**: Multiple simultaneous game sessions with isolation
- **WebSocket Real-time**: Live updates via WebSocket connections
- **Error Handling**: Edge cases, invalid inputs, and error scenarios
- **Role-Based Gameplay**: Hidden roles, phase transitions, and security

## Test Coverage

**26 test scenarios** across 5 feature files:

| Feature File | Scenarios | Description |
|--------------|-----------|-------------|
| `game_lifecycle.feature` | 3 | Basic game creation, multi-turn gameplay, resource cleanup |
| `concurrent_games.feature` | 4 | Multiple games, isolation, concurrent load testing |
| `websocket_realtime.feature` | 6 | WebSocket connections, broadcasts, real-time updates |
| `error_handling.feature` | 8 | Error cases, non-existent resources, edge cases |
| `role_based_gameplay.feature` | 5 | Hidden roles, phase transitions, security validation |

## Running the Tests

### Run all e2e tests:
```bash
cd backend
pytest tests/e2e/
```

### Run tests with verbose output:
```bash
pytest tests/e2e/ -v
```

### Run specific feature:
```bash
pytest tests/e2e/ -k "lifecycle"
pytest tests/e2e/ -k "websocket"
pytest tests/e2e/ -k "concurrent"
```

### Run with BDD marker:
```bash
pytest -m bdd
pytest -m e2e
```

### Generate coverage report:
```bash
pytest tests/e2e/ --cov=wolfai --cov-report=html
```

## Test Results

Current test status: **20/26 passing (77%)**

### Passing Scenarios (20):
- ✅ End game cleans up resources
- ✅ Create and manage multiple games simultaneously
- ✅ Actions in one game don't affect other games
- ✅ Heavy concurrent load
- ✅ Client handles disconnection gracefully
- ✅ WebSocket connections closed when game ends
- ✅ Access non-existent game (404 handling)
- ✅ Submit action to non-existent game (404 handling)
- ✅ End non-existent game (404 handling)
- ✅ Double-end game protection
- ✅ WebSocket connection to non-existent game
- ✅ Handle invalid action data
- ✅ Rapid sequential actions (50 actions)
- ✅ Games list remains consistent
- ✅ Players have hidden roles (security)
- ✅ Actions don't reveal actor identity
- ✅ Multiple players with different roles
- And more...

### Known Issues (6 failing):
- ⚠️ Some phase transition tests need adjustment
- ⚠️ Some WebSocket broadcast tests need timing fixes

## Feature Files

Feature files are written in Gherkin syntax and located in `features/`:

### Example Scenario:

```gherkin
Scenario: Create and complete a basic game
  When I create a new game
  Then the game should be created successfully
  And the game should appear in the active games list
  When I get the game state
  Then the game phase should be "initialized"
  When I submit action "player1 speaks" by player "player1"
  Then the action should be recorded successfully
  When I end the game
  Then the game should not appear in the active games list
```

## Step Definitions

Step definitions are implemented in `test_game_features.py` and provide the glue code between Gherkin scenarios and Python test code.

### Key Step Categories:

- **Game Creation**: Create games, manage multiple sessions
- **Game State**: Query and verify game state
- **Actions**: Submit player actions, verify recording
- **WebSocket**: Connect, disconnect, verify broadcasts
- **Assertions**: Validate responses, states, and behaviors
- **Error Handling**: Test error conditions and edge cases

## Architecture

```
tests/e2e/
├── README.md                    # This file
├── __init__.py                  # Package marker
├── conftest.py                  # Pytest configuration
├── features/                    # Gherkin feature files
│   ├── game_lifecycle.feature
│   ├── concurrent_games.feature
│   ├── websocket_realtime.feature
│   ├── error_handling.feature
│   └── role_based_gameplay.feature
└── test_game_features.py        # Step definitions
```

## Dependencies

- **pytest-bdd**: Cucumber/Gherkin support for pytest
- **pytest**: Test framework
- **pytest-asyncio**: Async test support
- **httpx**: Async HTTP client
- **FastAPI TestClient**: HTTP and WebSocket testing
- **Starlette**: WebSocket test support

## Writing New Tests

### 1. Create a feature file:

```gherkin
Feature: My New Feature
  As a user
  I want to do something
  So that I achieve a goal

  Scenario: Test something
    Given some precondition
    When I do something
    Then something should happen
```

### 2. Add step definitions:

```python
from pytest_bdd import scenarios, given, when, then

scenarios("features/my_feature.feature")

@given("some precondition")
def setup_precondition(client, context):
    # Setup code
    pass

@when("I do something")
def do_something(client, context):
    # Action code
    response = client.post("/endpoint")
    context["response"] = response

@then("something should happen")
def verify_result(context):
    # Assertion code
    assert context["response"].status_code == 200
```

### 3. Run the new tests:

```bash
pytest tests/e2e/test_game_features.py::test_my_scenario -v
```

## Best Practices

1. **Use descriptive scenario names** that explain what is being tested
2. **Keep scenarios focused** on one behavior at a time
3. **Use Background** sections for common setup steps
4. **Use scenario outlines** for data-driven tests (not yet implemented)
5. **Maintain step reusability** across multiple scenarios
6. **Test both happy paths and error cases**
7. **Verify security properties** (e.g., roles not exposed)

## Continuous Integration

These tests run automatically in CI/CD pipelines. See `.github/workflows/ci.yml` for configuration.

## Troubleshooting

### Tests fail with "Step definition not found"
- Check that the step definition matches the feature file exactly
- Verify parsers are used correctly for parameterized steps

### WebSocket tests timeout
- Increase timeout values if needed
- Check that WebSocket connections are properly established
- Verify broadcast mechanisms are working

### Async tests not running
- Ensure pytest-asyncio is installed
- Add `@pytest.mark.asyncio` decorator if needed
- Check that async fixtures are properly configured

## Contributing

When adding new game features:

1. Write feature file first (BDD approach)
2. Implement step definitions
3. Verify tests fail (red)
4. Implement the feature
5. Verify tests pass (green)
6. Refactor if needed

## Resources

- [pytest-bdd Documentation](https://pytest-bdd.readthedocs.io/)
- [Gherkin Syntax](https://cucumber.io/docs/gherkin/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [WebSocket Testing with Starlette](https://www.starlette.io/testclient/)
