"""Agents package for Wolf AI."""

# Lazy import to avoid loading deprecated LangChain dependencies
# Import PrologAgent directly when needed: from wolfai.agents.prolog import PrologAgent

__all__ = ['PrologAgent']


def __getattr__(name):
    """Lazy import for agents to avoid loading deprecated dependencies."""
    if name == 'PrologAgent':
        from .prolog import PrologAgent
        return PrologAgent
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
