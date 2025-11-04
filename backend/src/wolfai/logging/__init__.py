"""Enhanced logging management for WolfAI."""

import logging
import sys


def configure_basic_logging(level=logging.DEBUG, name=None):
    """Configure basic logging with standard format.

    Args:
        level: Logging level (default: DEBUG)
        name: Logger name to return (default: __name__ from caller)

    Returns:
        Logger instance
    """
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        stream=sys.stdout
    )
    return logging.getLogger(name or __name__)


# Default import mechanism with graceful fallback
try:
    from .otel import (
        ObservabilityConfig,
        OpenTelemetryConfig,
        OTelOperationTimer,
        getLogger,
        otel_log_call,
        setup_otel_logging,
    )
except ImportError as e:
    import logging
    logging.warning(f"OpenTelemetry logging import failed: {e}")

    # Provide no-op fallback implementations
    def setup_otel_logging(*args, **kwargs):
        """Fallback logging setup when OpenTelemetry is unavailable."""
        logging.basicConfig(level=logging.INFO)

    def otel_log_call(func=None, **kwargs):
        """Fallback decorator that passes through function without tracing."""
        def decorator(f):
            return f
        return decorator if func is None else decorator(func)

    class ObservabilityConfig:
        """Fallback configuration when OpenTelemetry is unavailable."""
        DEFAULT_SERVICE_NAME = "wolfai"

    class OpenTelemetryConfig:
        """No-op OpenTelemetry configuration."""
        pass

    class OTelOperationTimer:
        """No-op operation timer."""
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args, **kwargs):
            pass

# Re-export key components
__all__ = [
    'configure_basic_logging',
    'setup_otel_logging',
    'otel_log_call',
    'ObservabilityConfig',
    'OpenTelemetryConfig',
    'OTelOperationTimer',
    'getLogger'
]
