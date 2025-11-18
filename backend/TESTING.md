# Testing Guide

## Running Tests

### Quick Start
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_api.py

# Run with verbose output
pytest -v

# Run tests in parallel
pytest -n auto
```

### Test Coverage

**Current Status:** 71 passing, 13 skipped

**Test Breakdown:**
- **27 E2E/BDD tests** - Game lifecycle, error handling, role-based gameplay
- **5 API tests** - REST endpoints, WebSocket, state management
- **4 WebSocket tests** - Real-time updates, broadcasts, multiple clients
- **35 Tool tests** - MCP utilities, prompts

## Skipped Tests

### WebSocket BDD Tests (4 skipped)
**Location:** `tests/e2e/test_game_features.py`

**Why skipped:** BDD framework doesn't support WebSocket context managers across step definitions

**Replacement:** Comprehensive WebSocket tests in `tests/test_websocket_async.py` (4 passing)

**Status:** ✅ Fully covered by replacement tests

### Prolog Tests (9 skipped)
**Location:**
- `tests/agents/test_prolog.py`
- `tests/agents/test_prolog_agent.py`
- `tests/tools/pl/test_prolog.py`
- `tests/tools/pl/test_prolog_chains.py`
- `tests/tools/pl/test_prolog_chain_integration.py`

**Why skipped:** SWI-Prolog not installed on system

**To enable:**
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y swi-prolog

# macOS
brew install swi-prolog

# Verify installation
swipl --version
python -c "import pyswip; print('PySwip OK')"
```

**Then run:**
```bash
pytest tests/agents/test_prolog.py -v
pytest tests/tools/pl/ -v
```

## Test Types

### Unit Tests
Located in `tests/` - Test individual components in isolation

### Integration Tests
Located in `tests/test_api.py`, `tests/test_websocket_async.py` - Test component interactions

### E2E/BDD Tests
Located in `tests/e2e/` - Behavior-driven tests using Cucumber/Gherkin syntax

**Feature files:** `tests/e2e/features/*.feature`
**Step definitions:** `tests/e2e/test_game_features.py`

## Running in CI

Tests automatically run in GitHub Actions on every push/PR. See `.github/workflows/ci.yml`

The CI environment has SWI-Prolog pre-installed, so all tests run there.

## Writing Tests

### Adding a new test
```python
def test_my_feature():
    """Test that my feature works."""
    # Arrange
    game = create_game()

    # Act
    result = game.do_something()

    # Assert
    assert result == expected_value
```

### Adding a BDD scenario
1. Add scenario to `tests/e2e/features/*.feature`
2. Add step definitions to `tests/e2e/test_game_features.py`
3. Run with `pytest tests/e2e/test_game_features.py`

## Test Configuration

Configuration in `pyproject.toml`:
```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
markers = [
    "slow: marks tests as slow",
    "integration: marks integration tests",
    "e2e: marks end-to-end tests",
]
```
