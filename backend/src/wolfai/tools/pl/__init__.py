"""Runtime components for WolfAI."""

from typing import Any


# Lazy imports to avoid requiring SWI-Prolog at import time
# Import directly when needed: from wolfai.tools.pl.prolog import PrologState, ...

__all__ = ["PrologResult", "PrologState", "_execute", "consult"]


def __getattr__(name: str) -> Any:
    """Lazy import for prolog tools to avoid requiring SWI-Prolog at import time."""
    if name in __all__:
        from .prolog import PrologResult, PrologState, _execute, consult  # noqa: F401
        return locals()[name]
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)
