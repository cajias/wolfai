# Python Linting in WolfAI

This document describes the Python linting setup in the WolfAI project.

## Linting Tools

We use two complementary linting tools:

### 1. Ruff (Primary Linter)
[Ruff](https://github.com/astral-sh/ruff) is our primary Python linter - a fast, comprehensive linter written in Rust that combines the functionality of:

- Flake8 (and many of its plugins)
- isort
- pyupgrade
- autoflake
- Pylint refactor checks
- and more

### 2. Pylint (Duplicate Code Detection)
[Pylint](https://pylint.pycqa.org/) is used specifically for duplicate code detection (R0801). It finds similar code blocks across files that could be refactored into shared functions or modules.

## Configuration

### Ruff Configuration

Ruff is configured in the `backend/pyproject.toml` file with comprehensive linting rules:

```toml
[tool.ruff]
line-length = 100

[tool.ruff.lint]
# Enable comprehensive linting rules
select = ["E", "F", "I", "B", "W", "C90", "PLR", "SIM"]

# Only ignore rules that genuinely conflict with Black or are false positives
ignore = [
    "E501",  # Line too long (let Black handle this)
]

# Avoid trying to fix flake8-bugbear (`B`) violations automatically
unfixable = ["B"]

[tool.ruff.lint.mccabe]
# Flag overly complex code (McCabe complexity > 10).
max-complexity = 10

[tool.ruff.lint.pylint]
# Enforce reasonable function complexity limits
max-args = 5
max-branches = 12
max-returns = 6
max-statements = 50

# Ignore `E402` (import violations) in all `__init__.py` files
[tool.ruff.lint.per-file-ignores]
"__init__.py" = ["E402"]
"tests/**" = ["B008", "PLR2004"]  # Allow magic values in tests
```

### Rule Categories Enabled

- **E, W**: pycodestyle errors and warnings
- **F**: Pyflakes (undefined names, unused imports, etc.)
- **I**: isort (import sorting)
- **B**: flake8-bugbear (design issues)
- **C90**: McCabe complexity checking (max complexity 10)
- **PLR**: Pylint refactor recommendations
- **SIM**: Simplification suggestions

### Complexity Limits

The configuration enforces the following limits to maintain code quality:
- Maximum function arguments: 5
- Maximum branches per function: 12
- Maximum return statements: 6
- Maximum statements per function: 50
- Maximum cyclomatic complexity: 10

### Pylint Configuration

Pylint is configured in `backend/.pylintrc` for focused duplicate code detection:

```ini
[MASTER]
# Focus only on duplicate code detection
disable=all
enable=duplicate-code

# Use multiple processes for speed
jobs=0

[SIMILARITIES]
# Minimum lines number of a similarity.
min-similarity-lines=4

# Ignore comments when computing similarities.
ignore-comments=yes

# Ignore docstrings when computing similarities.
ignore-docstrings=yes

# Ignore imports when computing similarities.
ignore-imports=yes

# Signatures are removed from the similarity computation
ignore-signatures=yes
```

This configuration:
- Only enables the `duplicate-code` (R0801) check for performance
- Detects code blocks with 4+ similar lines
- Ignores comments, docstrings, imports, and signatures when comparing
- Uses multiple processes for faster analysis

## Running the Linter

You can run the linter using the following commands:

```bash
# Run Ruff on the entire project (from root directory)
npm run lint:py

# Check for duplicate code blocks
npm run lint:py:dupes

# Run Ruff directly in the backend directory
cd backend
python3 -m ruff check src/ tests/

# Run duplicate detection directly
cd backend
python3 -m pylint --rcfile=.pylintrc src/ tests/

# Fix automatically fixable issues
python3 -m ruff check --fix src/ tests/

# Run the automated fix script
npm run lint:py:fix
# or
./scripts/fix-python-issues.sh
```

## Fixing Issues

Many issues can be fixed automatically using Ruff's `--fix` option. We've provided a script to help with this:

```bash
npm run lint:py:fix
```

This script will:

1. Run Ruff with the `--fix` option to fix automatically fixable issues
2. Sort imports with Ruff
3. Format the code with Black (if available)

## Current Status

### Ruff Linting
✅ **All linting checks pass!** The codebase is fully compliant with our strict linting rules.

All 111 previously identified issues have been fixed, including:
- Import sorting and organization
- Code formatting and whitespace
- All issues were resolved using Ruff's auto-fix capabilities

### Duplicate Code Detection
⚠️ **Code Quality: 9.96/10** - Some duplicate code blocks detected.

Current duplicate code findings:
- **Logging setup**: Similar logging configuration in multiple files
- **Pytest fixtures**: SWI-Prolog availability checks duplicated in conftest files
- **MCP message structures**: Similar message construction patterns across test files

These duplicates are opportunities for refactoring but don't block development. Consider extracting common patterns into shared utilities when appropriate.

## Best Practices

When writing Python code for this project, follow these best practices to maintain clean, maintainable code:

### Exception Handling (B904)

Always preserve exception context when re-raising exceptions:

**Best Practice**: Use `raise ... from err` to preserve tracebacks

  ```python
  # Before
  try:
      do_something()
  except Exception as e:
      raise ValueError("Something went wrong")

  # After
  try:
      do_something()
  except Exception as e:
      raise ValueError("Something went wrong") from e
  ```

### Function Complexity (C901)

Keep functions focused and simple to improve readability and maintainability:

**Best Practice**: Break down complex functions into smaller, more focused functions

  ```python
  # Before
  def complex_function():
      # 50+ lines of code with many branches

  # After
  def complex_function():
      result1 = step1()
      result2 = step2(result1)
      return step3(result2)

  def step1():
      # Focused logic for step 1

  def step2(data):
      # Focused logic for step 2

  def step3(data):
      # Focused logic for step 3
  ```

### Abstract Base Classes (B024, B027)

Properly mark abstract methods to make interfaces clear:

**Best Practice**: Add `@abstractmethod` decorator to methods that must be implemented by subclasses

  ```python
  # Before
  class WolfAIPlugin(abc.ABC):
      def register_commands(self, cli):
          """Register commands with the CLI."""
          pass

  # After
  class WolfAIPlugin(abc.ABC):
      @abstractmethod
      def register_commands(self, cli):
          """Register commands with the CLI."""
          pass
  ```

### Caching (B019)

Avoid memory leaks when using caching:

**Best Practice**: Use `@lru_cache` on module-level functions, not instance methods

  ```python
  # Before
  class MyClass:
      @lru_cache(maxsize=128)
      def cached_method(self, arg):
          return expensive_operation(arg)

  # After
  @lru_cache(maxsize=128)
  def _cached_function(arg):
      return expensive_operation(arg)

  class MyClass:
      def cached_method(self, arg):
          return _cached_function(arg)
  ```

## CI Integration

Ruff should be integrated into the CI pipeline to run automatically on all pull requests. Add the following to your CI configuration:

```yaml
# Example for GitHub Actions
- name: Lint Python code
  run: npm run lint:py
```

## Available Scripts

- `npm run lint:py` - Run Ruff linter on Python code
- `npm run lint:py:dupes` - Check for duplicate code blocks
- `npm run lint:py:fix` - Auto-fix linting issues
- `npm run test:py` - Run Python tests

## Resources

- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [Ruff Rules Reference](https://docs.astral.sh/ruff/rules/)
- [Pylint Documentation](https://pylint.pycqa.org/)
- [Pylint Duplicate Code Detection](https://pylint.pycqa.org/en/latest/user_guide/messages/refactor/duplicate-code.html)
- [Python Code Quality Tools](https://realpython.com/python-code-quality/)
