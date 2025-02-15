"""Enhanced logging utility with OpenTelemetry integration."""

import contextlib
import functools
import logging
import os
import time
from typing import (
    Callable,
    Optional,
    TypeVar,
    Union,
    cast
)

# OpenTelemetry imports
from opentelemetry import trace, context
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.semconv.trace import SpanAttributes

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
            Configured tracer
        """
        return trace.get_tracer(name)


def otel_log_call(
    func: Optional[Callable[..., T]] = None,
    *,
    log_level: int = logging.INFO,
    log_args: bool = False,
    log_result: bool = False,
    performance_warning: bool = True
) -> Union[Callable[..., T], Callable[[Callable[..., T]], Callable[..., T]]]:
    """
    Decorator that combines logging with OpenTelemetry tracing.

    Args:
        func: Function to decorate
        log_level: Logging level
        log_args: Log function arguments
        log_result: Log function return value
        performance_warning: Log warning for slow function calls

    Returns:
        Decorated function with logging and tracing
    """
    # Get the global tracer
    tracer = OpenTelemetryConfig().get_tracer(func.__module__ if func else __name__)

    def decorator(f: Callable[..., T]) -> Callable[..., T]:
        # Use module logger or create a default one
        logger = logging.getLogger(f.__module__ if f.__module__ != '__main__' else 'root')

        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            # Start a new span
            span_name = f.__qualname__
            with tracer.start_as_current_span(span_name) as span:
                # Add attributes to the span
                span.set_attribute(SpanAttributes.CODE_FUNCTION, span_name)
                span.set_attribute(SpanAttributes.CODE_NAMESPACE, f.__module__)

                # Log function arguments if requested
                if log_args:
                    span.set_attribute("function.args", str(args))
                    span.set_attribute("function.kwargs", str(kwargs))
                    logger.log(log_level,
                        f"Calling {span_name} "
                        f"(args: {args}, kwargs: {kwargs})"
                    )

                # Track execution time
                start_time = time.perf_counter()

                try:
                    # Execute function
                    result = f(*args, **kwargs)

                    # Log result if requested
                    if log_result:
                        span.set_attribute("function.result", str(result))
                        logger.log(log_level,
                            f"{span_name} result: {result}"
                        )

                    # Log execution time
                    end_time = time.perf_counter()
                    duration_ms = (end_time - start_time) * 1000
                    span.set_attribute("function.duration_ms", duration_ms)

                    # Performance logging
                    if performance_warning and duration_ms > ObservabilityConfig.PERFORMANCE_THRESHOLD_MS:
                        span.add_event("performance_warning", {
                            "duration_ms": duration_ms
                        })
                        logger.warning(
                            f"{span_name} exceeded performance threshold "
                            f"(duration: {duration_ms:.2f}ms)"
                        )

                    logger.log(log_level,
                        f"{span_name} executed "
                        f"(duration: {duration_ms:.2f}ms)"
                    )

                    return result

                except Exception as e:
                    # Mark span as failed and log exception
                    span.set_status(trace.Status(trace.StatusCode.ERROR))
                    span.record_exception(e)

                    # Log exception
                    logger.exception(
                        f"Error in {span_name}: {str(e)}"
                    )

                    raise

        return cast(Callable[..., T], wrapper)

    # Allow decorator to be used with or without parentheses
    if func is None:
        return decorator
    return decorator(func)


class OTelOperationTimer(contextlib.AbstractContextManager):
    """
    Context manager for timing operations with OpenTelemetry tracing.

    Usage:
        with OTelOperationTimer('database_query'):
            # operation code
    """

    def __init__(
        self,
        operation_name: str,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize operation timer.

        Args:
            operation_name: Name of the operation being monitored
            logger: Optional logger (defaults to root logger)
        """
        self.operation_name = operation_name
        self.logger = logger or logging.getLogger('root')
        self.tracer = OpenTelemetryConfig().get_tracer()
        self.start_time = None
        self.span = None

    def __enter__(self):
        """Start timing and tracing on context entry."""
        self.start_time = time.perf_counter()

        # Start a new span
        self.span = self.tracer.start_span(self.operation_name)
        context.attach(trace.set_span_in_context(self.span))

        self.logger.info(f"Starting {self.operation_name}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Log completion or exception and end tracing."""
        end_time = time.perf_counter()
        duration_ms = (end_time - self.start_time) * 1000

        if exc_type is None:
            # Successful completion
            self.span.set_status(trace.Status(trace.StatusCode.OK))
            self.logger.info(
                f"{self.operation_name} completed "
                f"(duration: {duration_ms:.2f}ms)"
            )

            # Performance warning
            if duration_ms > ObservabilityConfig.PERFORMANCE_THRESHOLD_MS:
                self.span.add_event("performance_warning", {
                    "duration_ms": duration_ms
                })
                self.logger.warning(
                    f"{self.operation_name} exceeded performance threshold "
                    f"(duration: {duration_ms:.2f}ms)"
                )
        else:
            # Exception occurred
            self.span.set_status(trace.Status(trace.StatusCode.ERROR))
            self.span.record_exception(exc_val)

            self.logger.error(
                f"{self.operation_name} failed "
                f"(duration: {duration_ms:.2f}ms): "
                f"{exc_type.__name__} - {exc_val}"
            )

        # End the span
        self.span.end()

        # Propagate any exception
        return False


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

    # Initialize OpenTelemetry configuration
    OpenTelemetryConfig()
