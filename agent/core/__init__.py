"""Core module namespace.

CrewAI-specific builders are intentionally not imported eagerly so lightweight
commands (status/trade simulation/validation) can run without CrewAI runtime.
"""

__all__ = []
