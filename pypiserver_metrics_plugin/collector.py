import time

from prometheus_client import (
    Counter,
    Gauge,
    Histogram,
    Info,
    CollectorRegistry,
    generate_latest,
    CONTENT_TYPE_LATEST,
)


class MetricsCollector:
    """
    Collects metrics for pypiserver operations.

    If prometheus_client is not installed, this class does nothing
    (all metric recording becomes a no-op).
    """

    def __init__(self) -> None:
        # Create a separate registry for pypiserver metrics
        self.registry = CollectorRegistry()

        # HTTP Request Metrics
        self.http_requests_total = Counter(
            "pypiserver_http_requests_total",
            "Total HTTP requests",
            ["method", "endpoint", "status_code"],
            registry=self.registry,
        )

        self.http_request_duration_seconds = Histogram(
            "pypiserver_http_request_duration_seconds",
            "HTTP request duration in seconds",
            ["method", "endpoint", "status_code"],
            buckets=[
                0.005,
                0.01,
                0.025,
                0.05,
                0.075,
                0.1,
                0.25,
                0.5,
                0.75,
                1.0,
                2.5,
                5.0,
                7.5,
                10.0,
            ],
            registry=self.registry,
        )

        # Package Operation Metrics
        self.package_downloads_total = Counter(
            "pypiserver_package_downloads_total",
            "Total package downloads",
            ["package_name", "filename"],
            registry=self.registry,
        )

        self.package_uploads_total = Counter(
            "pypiserver_package_uploads_total",
            "Total successful package uploads",
            ["package_name", "user"],
            registry=self.registry,
        )

        self.package_upload_failures_total = Counter(
            "pypiserver_package_upload_failures_total",
            "Total failed package uploads",
            ["reason"],
            registry=self.registry,
        )

        self.package_removals_total = Counter(
            "pypiserver_package_removals_total",
            "Total package removals",
            ["package_name", "user"],
            registry=self.registry,
        )

        # Repository State Metrics
        self.packages_total = Gauge(
            "pypiserver_packages_total",
            "Current number of package files",
            registry=self.registry,
        )

        self.projects_total = Gauge(
            "pypiserver_projects_total",
            "Current number of unique projects",
            registry=self.registry,
        )

        # Search & Discovery Metrics
        self.searches_total = Counter(
            "pypiserver_searches_total",
            "Total search operations",
            ["search_type"],
            registry=self.registry,
        )

        self.simple_index_requests_total = Counter(
            "pypiserver_simple_index_requests_total",
            "Total PEP 503 simple index requests",
            ["project_name"],
            registry=self.registry,
        )

        # Authentication Metrics
        self.auth_attempts_total = Counter(
            "pypiserver_auth_attempts_total",
            "Total authentication attempts",
            ["action", "result"],
            registry=self.registry,
        )

        # Error Metrics
        self.errors_total = Counter(
            "pypiserver_errors_total",
            "Total errors",
            ["endpoint", "error_type", "status_code"],
            registry=self.registry,
        )

        # System Info
        self.server_info = Info(
            "pypiserver", "PyPI server information", registry=self.registry
        )

        # Uptime
        self.start_time = time.time()
        self.uptime_seconds = Gauge(
            "pypiserver_uptime_seconds",
            "Server uptime in seconds",
            registry=self.registry,
        )

    def record_http_request(
            self, method: str, endpoint: str, status_code: int, duration: float
    ) -> None:
        """Record an HTTP request with timing."""
        self.http_requests_total.labels(
            method=method, endpoint=endpoint, status_code=status_code
        ).inc()

        self.http_request_duration_seconds.labels(
            method=method, endpoint=endpoint, status_code=status_code
        ).observe(duration)

    def record_download(self, package_name: str, filename: str) -> None:
        """Record a package download."""
        self.package_downloads_total.labels(
            package_name=package_name, filename=filename
        ).inc()

    def record_upload(self, package_name: str, user: str) -> None:
        """Record a successful package upload."""
        self.package_uploads_total.labels(
            package_name=package_name, user=user or "anonymous"
        ).inc()

    def record_upload_failure(self, reason: str) -> None:
        """Record a failed package upload."""
        self.package_upload_failures_total.labels(reason=reason).inc()

    def record_removal(self, package_name: str, user: str) -> None:
        """Record a package removal."""
        self.package_removals_total.labels(
            package_name=package_name, user=user or "anonymous"
        ).inc()

    def update_package_counts(
            self, package_count: int, project_count: int
    ) -> None:
        """Update repository state metrics."""
        self.packages_total.set(package_count)
        self.projects_total.set(project_count)

    def record_search(self, search_type: str) -> None:
        """Record a search operation."""
        self.searches_total.labels(search_type=search_type).inc()

    def record_simple_index_request(self, project_name: str) -> None:
        """Record a PEP 503 simple index request."""
        self.simple_index_requests_total.labels(
            project_name=project_name
        ).inc()

    def record_auth_attempt(self, action: str, success: bool) -> None:
        """Record an authentication attempt."""
        result = "success" if success else "failure"
        self.auth_attempts_total.labels(action=action, result=result).inc()

    def record_error(
            self, endpoint: str, error_type: str, status_code: int
    ) -> None:
        """Record an error."""
        self.errors_total.labels(
            endpoint=endpoint, error_type=error_type, status_code=status_code
        ).inc()

    def set_server_info(
            self, version: str, backend_type: str, fallback_url: str
    ) -> None:
        """Set server information."""
        self.server_info.info(
            {
                "version": version,
                "backend_type": backend_type,
                "fallback_url": fallback_url,
            }
        )

    def update_uptime(self) -> None:
        """Update server uptime."""
        self.uptime_seconds.set(time.time() - self.start_time)

    def generate_metrics(self) -> tuple[bytes, str]:
        """
        Generate Prometheus metrics output.

        Returns:
            Tuple of (metrics_bytes, content_type)
        """
        # Update uptime before generating metrics
        self.update_uptime()

        return generate_latest(self.registry), CONTENT_TYPE_LATEST