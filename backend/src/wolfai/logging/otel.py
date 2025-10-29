"""Enhanced logging utility with OpenTelemetry integration."""

import contextlib
import logging
import os
from typing import (
    TypeVar
)

# OpenTelemetry imports
try:
    from opentelemetry import trace
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.instrumentation.logging import LoggingInstrumentor
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    OPENTELEMETRY_AVAILABLE = True
except ImportError:
    OPENTELEMETRY_AVAILABLE = False


def getLogger(name: str) -> logging.Logger:
    """
    Get or create a logger instance for the given name.

    Args:
        name (str): The name of the logger.

    Returns:
        logging.Logger: Configured logger instance.
    """
    logger = logging.getLogger(name)
    if not logger.hasHandlers():
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(ObservabilityConfig.LOG_FORMAT))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


# Type variable for generic function return type
T = TypeVar('T')

class ObservabilityConfig:
    """
    Centralized configuration for observability features.
    """
    # Configurable constants with environment variable overrides
    PERFORMANCE_THRESHOLD_MS: int = int(os.getenv('WOLFAI_PERF_THRESHOLD_MS', '100'))
    OTLP_ENDPOINT: str = os.getenv('WOLFAI_OTLP_ENDPOINT', 'http://localhost:4318/v1/traces')
    DEFAULT_SERVICE_NAME: str = os.getenv('WOLFAI_SERVICE_NAME', 'wolfai')
    LOG_FORMAT: str = os.getenv(
        'WOLFAI_LOG_FORMAT',
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    TRACE_SAMPLE_RATE: float = float(os.getenv('WOLFAI_TRACE_SAMPLE_RATE', '1.0'))

    @classmethod
    def update_config(cls, **kwargs):
        """
        Update configuration at runtime.

        Args:
            **kwargs: Configuration key-value pairs to update
        """
        for key, value in kwargs.items():
            if hasattr(cls, key):
                setattr(cls, key, value)


class OpenTelemetryConfig:
    """
    Centralized configuration for OpenTelemetry integration.
    """
    _instance = None

    def __new__(cls):
        if not cls._instance:
            cls._instance = super().__new__(cls)
            cls._initialize_tracer()
        return cls._instance

    @classmethod
    def _initialize_tracer(cls):
        """
        Initialize the global tracer provider.
        """
        if not OPENTELEMETRY_AVAILABLE:
            return

        # Setup tracing
        trace.set_tracer_provider(TracerProvider())

        # Optional OTLP exporter (can be configured)
        try:
            otlp_exporter = OTLPSpanExporter(
                endpoint=ObservabilityConfig.OTLP_ENDPOINT
            )
            span_processor = BatchSpanProcessor(otlp_exporter)
            trace.get_tracer_provider().add_span_processor(span_processor)
        except Exception as e:
            print(f"Could not configure OTLP exporter: {e}")

        # Instrument logging
        LoggingInstrumentor().instrument()

    @classmethod
    def get_tracer(cls, name: str = __name__):
        """
        Get a tracer for the given name.

        Args:
            name: Name of the tracer (defaults to current module)

        Returns:
            Configured tracer or a no-op tracer if not available
        """
        if OPENTELEMETRY_AVAILABLE:
            return trace.get_tracer(name)

        # Return a no-op tracer
        class NoOpTracer:
            def start_as_current_span(self, *args, **kwargs):
                return contextlib.nullcontext()

        return NoOpTracer()


def setup_otel_logging(
    service_name: str = ObservabilityConfig.DEFAULT_SERVICE_NAME,
    log_level: int = logging.INFO
):
    """
    Configure comprehensive logging and tracing setup.

    Args:
        service_name: Name of the service for tracing
        log_level: Logging level
    """
    # Configure logging
    logging.basicConfig(
        level=log_level,
        format=ObservabilityConfig.LOG_FORMAT
    )

    # Only attempt OpenTelemetry setup if available
    if OPENTELEMETRY_AVAILABLE:
        try:
            OpenTelemetryConfig()
        except Exception as e:
            logging.warning(f"OpenTelemetry initialization failed: {e}")
            logging.warning("Continuing without OpenTelemetry tracing")
    else:
        logging.warning("OpenTelemetry not available. Using standard logging.")


def otel_log_call(func=None, **kwargs):
    """
    Decorator to log function inputs and outputs.

    Args:
        func: The function to wrap
        **kwargs: Additional options for tracing/logging (optional)
    """
    if func is None:
        return lambda f: otel_log_call(f, **kwargs)

    def wrapper(*args, **inner_kwargs):
        logger = logging.getLogger(func.__module__)
        logger.info(f"Calling {func.__name__} with args: {args}, kwargs: {inner_kwargs}")

        span = None
        if OPENTELEMETRY_AVAILABLE:
            tracer = OpenTelemetryConfig.get_tracer(func.__module__)
            span = tracer.start_as_current_span(func.__name__, **kwargs)

        try:
            # Trace execution of the function
            with span if span else contextlib.nullcontext():
                result = func(*args, **inner_kwargs)

            logger.info(f"{func.__name__} returned: {result}")
            return result

        except Exception as e:
            logger.exception(f"Exception in {func.__name__}: {e}")
            raise

    return wrapper


class OTelOperationTimer:
    """
    Timer for measuring operation performance and logging to OpenTelemetry.
    """

    def __init__(self, operation_name: str, **span_kwargs):
        """
        Initialize the operation timer.

        Args:
            operation_name (str): The name of the operation being timed.
            **span_kwargs: Additional arguments for the span.
        """
        self.operation_name = operation_name
        self.span_kwargs = span_kwargs
        self.start_time = None
        self.span = None

    def __enter__(self):
        """
        Start the timer and OpenTelemetry span.
        """
        import time
        self.start_time = time.perf_counter()

        if OPENTELEMETRY_AVAILABLE:
            tracer = OpenTelemetryConfig.get_tracer(__name__)
            self.span = tracer.start_as_current_span(self.operation_name, **self.span_kwargs)
            self.span.__enter__()

        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Stop the timer and OpenTelemetry span, and log the duration.
        """
        import time
        duration_ms = (time.perf_counter() - self.start_time) * 1000

        if OPENTELEMETRY_AVAILABLE and self.span:
            self.span.set_attribute("operation.duration_ms", duration_ms)
            self.span.__exit__(exc_type, exc_value, traceback)

        logger = logging.getLogger(__name__)
        logger.info(f"Operation '{self.operation_name}' completed in {duration_ms:.2f}ms")


