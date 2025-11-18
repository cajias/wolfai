#!/bin/bash

# Fix Python linting issues in the wolfai project
# This script runs Ruff with auto-fix enabled to resolve common linting issues

set -e  # Exit on error

echo "🔍 Running Ruff auto-fix on Python code..."

# Navigate to backend directory
cd "$(dirname "$0")/../backend" || exit 1

# Check if poetry is installed
if ! command -v poetry &> /dev/null; then
    echo "❌ Poetry is not installed. Please install Poetry first."
    exit 1
fi

# Install dependencies if needed
echo "📦 Ensuring dependencies are installed..."
poetry install --with dev --no-interaction

# Run Ruff with auto-fix
echo "🔧 Fixing automatically fixable issues with Ruff..."
poetry run ruff check --fix src/ tests/ || true

# Sort imports with Ruff
echo "📋 Organizing imports..."
poetry run ruff check --select I --fix src/ tests/ || true

# Format code if Black is available
if poetry run black --version &> /dev/null; then
    echo "✨ Formatting code with Black..."
    poetry run black src/ tests/
fi

echo "✅ Python linting fixes complete!"
echo ""
echo "Run 'npm run lint:py' or 'poetry run ruff check src/ tests/' to see remaining issues."
