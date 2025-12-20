"""Telemetry and observability for the AI Chat Service.

Based on ticket_service/telemetry.py pattern.
"""

import time
from typing import cast

from fastapi import Request, Response
from prometheus_client import Counter, Gauge, Histogram, generate_latest
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

# ============================================================================
# CONSTANTS
# ============================================================================

HTTP_SUCCESS_MIN = 200
HTTP_SUCCESS_MAX = 300
HTTP_ERROR_MIN = 400
HTTP_SERVER_ERROR = 500

# ============================================================================
# METRICS DEFINITIONS
# ============================================================================

# Request duration histogram (latency tracking)
# AI Chat requests might be slower than Ticket ops, so we adapt buckets if needed,
# but keeping consistency with ticket_service for now or extending the tail.
request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint", "status_code"],
    buckets=(0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0), # Extended for AI latency
)

# Request counter (success/failure tracking)
request_count = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"],
)

# Success rate counter
request_success_total = Counter(
    "http_requests_success_total",
    "Total successful HTTP requests (2xx status codes)",
    ["method", "endpoint"],
)

# Failure rate counter
request_failure_total = Counter(
    "http_requests_failure_total",
    "Total failed HTTP requests (4xx, 5xx status codes)",
    ["method", "endpoint", "status_code"],
)

# Active requests gauge
active_requests = Gauge(
    "http_requests_active",
    "Number of active HTTP requests",
    ["method", "endpoint"],
)


# ============================================================================
# MIDDLEWARE
# ============================================================================


class PrometheusMiddleware(BaseHTTPMiddleware):
    """Middleware to collect Prometheus metrics for all HTTP requests."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """Process request and collect metrics."""
        # Skip metrics endpoint itself
        if request.url.path == "/metrics":
            return await call_next(request)

        method = request.method
        endpoint = request.url.path

        # Track active requests
        active_requests.labels(method=method, endpoint=endpoint).inc()

        # Track request duration
        start_time = time.time()

        try:
            response: Response = await call_next(request)
        except Exception:
            # Track exceptions as failures
            duration = time.time() - start_time
            request_duration_seconds.labels(
                method=method, endpoint=endpoint, status_code=HTTP_SERVER_ERROR
            ).observe(duration)

            request_count.labels(
                method=method, endpoint=endpoint, status_code=HTTP_SERVER_ERROR
            ).inc()
            request_failure_total.labels(
                method=method, endpoint=endpoint, status_code=HTTP_SERVER_ERROR
            ).inc()

            raise
        else:
            status_code = response.status_code

            # Record metrics
            duration = time.time() - start_time
            request_duration_seconds.labels(
                method=method, endpoint=endpoint, status_code=status_code
            ).observe(duration)

            request_count.labels(method=method, endpoint=endpoint, status_code=status_code).inc()

            # Track success/failure
            if HTTP_SUCCESS_MIN <= status_code < HTTP_SUCCESS_MAX:
                request_success_total.labels(method=method, endpoint=endpoint).inc()
            elif status_code >= HTTP_ERROR_MIN:
                request_failure_total.labels(
                    method=method, endpoint=endpoint, status_code=status_code
                ).inc()

            return response

        finally:
            # Decrement active requests
            active_requests.labels(method=method, endpoint=endpoint).dec()


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_metrics() -> bytes:
    """Get Prometheus metrics in text format."""
    return cast("bytes", generate_latest())
