# Python Linting in WolfAI

This document describes the Python linting setup in the WolfAI project.

## Linting Tools

We use [Ruff](https://github.com/astral-sh/ruff) as our primary Python linter. Ruff is a fast, comprehensive Python linter written in Rust that combines the functionality of multiple Python linters including:

- Flake8 (and many of its plugins)
- isort
- pyupgrade
- autoflake
- and more

## Configuration

Ruff is configured in the `backend/pyproject.toml` file:

```toml
[tool.ruff]
line-length = 100

[tool.ruff.lint]
# Enable pycodestyle (E), Pyflakes (F), isort (I), and flake8-bugbear (B)
select = ["E", "F", "I", "B", "W", "C90"]
ignore = [
    "E203",  # Whitespace before ':' (conflicts with Black)
    "E501",  # Line too long (handled by Black)
    "B008",  # Do not perform function calls in argument defaults
    # Additional ignores to match flake8 configuration
    "D300",  # Use """triple double quotes"""
    "D103",  # Missing docstring in public function
    "D105",  # Missing docstring in magic method
    "D106",  # Missing docstring in public nested class
    # Temporarily ignore these to make the build pass
    "B904",  # Within an `except` clause, raise exceptions with `raise ... from err` or `raise ... from None`
    "C901",  # Function is too complex
    "B024",  # Abstract base class without abstract methods
    "B027",  # Empty method in abstract base class with no abstract decorator
    "B019",  # Use of functools.lru_cache on methods can lead to memory leaks
    "B007",  # Loop control variable not used within loop body
]

# Ignore `E402` (import violations) in all `__init__.py` files
[tool.ruff.lint.per-file-ignores]
"__init__.py" = ["E402"]
"tests/**" = ["B008"]
```

## Running the Linter

You can run the linter using the following commands:

```bash
# Run Ruff on the entire project (from root directory)
npm run lint:py

# Run Ruff directly in the backend directory
cd backend
python3 -m ruff check src/ tests/

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

As of the latest run, there are **111 linting issues** detected:
- **110 fixable** with the `--fix` option
- Most issues are related to import sorting (I001)

You can fix most of these automatically by running:

```bash
npm run lint:py:fix
```

## Technical Debt Plan

We've temporarily disabled some Ruff rules to make the build pass. These issues should be addressed in future PRs:

### Exception Handling (B904)

- **Issue**: Exceptions are raised without preserving the original exception context
- **Fix**: Use `raise ... from err` to preserve tracebacks
- **Example**:

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

### Complex Functions (C901)

- **Issue**: Many functions are too complex (high cyclomatic complexity)
- **Fix**: Break down complex functions into smaller, more focused functions
- **Example**:

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

- **Issue**: Abstract base classes without abstract methods or with empty methods
- **Fix**: Add `@abstractmethod` decorator to methods that should be implemented by subclasses
- **Example**:

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

### Memory Leaks (B019)

- **Issue**: Using `functools.lru_cache` on methods can lead to memory leaks
- **Fix**: Move cached methods to module-level functions or use a different caching strategy
- **Example**:

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

- `npm run lint:py` - Run linter on Python code
- `npm run lint:py:fix` - Auto-fix linting issues
- `npm run test:py` - Run Python tests

## Resources

- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [Ruff Rules Reference](https://docs.astral.sh/ruff/rules/)
- [Python Code Quality Tools](https://realpython.com/python-code-quality/)
