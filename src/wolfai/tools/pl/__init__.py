"""Runtime components for WolfAI."""

from .prolog import PrologState, PrologResult, consult, _execute

__all__ = ['PrologState', 'PrologResult', 'consult', '_execute']
