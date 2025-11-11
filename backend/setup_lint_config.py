#!/usr/bin/env python
"""Setup script to link lint configuration from agentic-guardrails package.

This script uses the official Python API from the agentic-guardrails package
to locate the configuration file and creates a symlink at the expected location.

Ruff's extend directive can parse pyproject.toml files with [tool.ruff] sections,
so we link/copy the config as pyproject.toml (not pyproject-linters.toml).
"""

import shutil
import sys
from pathlib import Path


def setup_lint_config() -> None:
    """Create symlink to lint configuration from installed package."""
    try:
        # Import here to provide helpful error message if package not installed
        from lint_configs import get_python_config_path  # noqa: PLC0415
        
        # Get the config file path from the installed package
        config_source = get_python_config_path()
        
        if not config_source.exists():
            raise FileNotFoundError(f"Config file not found at {config_source}")
        
        # Create target directory if it doesn't exist
        backend_dir = Path(__file__).parent
        target_dir = backend_dir / "python"
        target_dir.mkdir(exist_ok=True)
        
        # Ruff can parse pyproject.toml files with [tool.ruff] sections
        # Name it pyproject.toml so ruff recognizes it
        target_file = target_dir / "pyproject.toml"
        
        # Remove existing file/symlink if it exists
        if target_file.exists() or target_file.is_symlink():
            target_file.unlink()
        
        try:
            # Try to create a symlink (works on Unix/Linux/macOS)
            target_file.symlink_to(config_source)
            print(f"✓ Lint configuration linked to {target_file}")
        except (OSError, NotImplementedError):
            # Fallback to copying on Windows or systems without symlink support
            shutil.copy2(config_source, target_file)
            print(f"✓ Lint configuration copied to {target_file}")
        
    except ImportError as e:
        print(f"⚠ Warning: agentic-guardrails package not installed: {e}", file=sys.stderr)
        print("  Install with: pip install agentic-guardrails", file=sys.stderr)
        url = "git+https://github.com/cajias/lint-configs.git@v1.0.0#subdirectory=python"
        print(f'  Or: pip install "agentic-guardrails @ {url}"', file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"⚠ Error setting up lint configuration: {e}", file=sys.stderr)
        print(f"  {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    setup_lint_config()
