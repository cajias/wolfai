"""Runtime components for WolfAI."""

# Lazy imports to avoid requiring SWI-Prolog at import time
# Import directly when needed: from wolfai.tools.pl.prolog import PrologState, ...

__all__ = ['PrologState', 'PrologResult', 'consult', '_execute']


def __getattr__(name):
    """Lazy import for prolog tools to avoid requiring SWI-Prolog at import time."""
    if name in __all__:
        from .prolog import PrologState, PrologResult, consult, _execute  # noqa: F401
        return locals()[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
