"""Enhanced logging management for WolfAI."""

# Default import mechanism with graceful fallback
try:
    from .otel import (
        setup_otel_logging,
        otel_log_call,
        ObservabilityConfig,
        OpenTelemetryConfig,
        OTelOperationTimer, getLogger
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
    'setup_otel_logging',
    'otel_log_call',
    'ObservabilityConfig',
    'OpenTelemetryConfig',
    'OTelOperationTimer',
    'getLogger'
]
