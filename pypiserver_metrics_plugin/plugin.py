import os
import time

from .collector import MetricsCollector


class MetricsPlugin:
    """
    Bottle plugin for Prometheus metrics collection.

    This plugin is completely self-contained and non-invasive. It:
    - Tracks HTTP requests via Bottle hooks
    - Auto-detects package operations (downloads, uploads, searches) from request patterns
    - Provides a /metrics endpoint for Prometheus scraping
    - Requires NO changes to route handlers

    Usage:
        from pypiserver_metrics_plugin import MetricsPlugin
        app.install(MetricsPlugin())
    """

    name = 'metrics'
    api = 2

    def __init__(self, metrics_endpoint="/metrics", **kwargs):
        """
        Initialize the metrics plugin.

        Args:
            metrics_endpoint: Path for the metrics endpoint (default: /metrics)
            **kwargs: Additional keyword arguments (for future extensibility)
        """
        self.metrics_endpoint = os.getenv("METRICS_ENDPOINT", metrics_endpoint)
        self.config = None
        self.collector = None

    def setup(self, app):
        """
        Setup the plugin when it's installed to the Bottle app.

        This method:
        - Extracts pypiserver config from the app
        - Initializes the metrics collector
        - Adds before_request and after_request hooks
        - Registers the /metrics endpoint
        """
        from pypiserver import __version__

        # Get pypiserver config from the Bottle app
        # pypiserver stores its config in app._pypiserver_config
        self.config = getattr(app, '_pypiserver_config', None)

        if not self.config:
            raise RuntimeError(
                "Cannot find pypiserver config. "
                "Ensure this plugin is used with a pypiserver Bottle app."
            )

        # Initialize metrics collector
        self.collector = MetricsCollector()

        # Set server info
        self.collector.set_server_info(
            version=__version__,
            backend_type=type(self.config.backend).__name__,
            fallback_url=getattr(self.config, 'fallback_url', None) or "none",
        )

        # Add hooks for tracking requests
        app.add_hook('before_request', self._before_request)
        app.add_hook('after_request', self._after_request)

        # Add metrics endpoint
        self._add_metrics_endpoint(app)

    def _before_request(self):
        """Hook called before each request to start timing."""
        from pypiserver.bottle_wrapper import request
        request._metrics_start_time = time.time()

    def _after_request(self):
        """Hook called after each request to record metrics."""
        from pypiserver.bottle_wrapper import request, response

        if not self.collector:
            return

        duration = time.time() - getattr(request, "_metrics_start_time", time.time())
        endpoint = request.path
        method = request.method
        status_code = str(response.status_code)

        # Record HTTP request metrics
        self.collector.record_http_request(
            method=method,
            endpoint=endpoint,
            status_code=status_code,
            duration=duration,
        )

        # Auto-detect and record application-specific metrics based on patterns
        self._record_application_metrics(request, response, status_code)

    def _record_application_metrics(self, request, response, status_code):
        """
        Auto-detect application operations from request patterns.

        This method inspects requests to determine what operation occurred
        and records appropriate metrics without requiring route handler changes.
        """
        from pypiserver.pkg_helpers import guess_pkgname_and_version

        path = request.path
        method = request.method

        # Detect package downloads: GET /packages/filename
        if method == "GET" and path.startswith("/packages/") and status_code == "200":
            filename = path.split("/packages/", 1)[-1].split("?")[0]
            if filename:
                pkg_info = guess_pkgname_and_version(filename)
                if pkg_info:
                    self.collector.record_download(
                        package_name=pkg_info[0],
                        filename=filename
                    )

        # Detect package uploads: POST / with :action=file_upload
        elif method == "POST" and path == "/" and status_code == "200":
            action = request.forms.get(":action", "")
            if action == "file_upload":
                # Try to extract package name from the uploaded file
                files = request.files
                if "content" in files:
                    uploaded_file = files.get("content")
                    if uploaded_file:
                        pkg_info = guess_pkgname_and_version(uploaded_file.raw_filename)
                        if pkg_info:
                            user = request.auth[0] if request.auth else "anonymous"
                            self.collector.record_upload(
                                package_name=pkg_info[0],
                                user=user
                            )

        # Detect searches: POST /RPC2 with search method
        elif method == "POST" and path == "/RPC2" and status_code == "200":
            # We've already processed this as a search
            self.collector.record_search(search_type="xmlrpc")

    def _add_metrics_endpoint(self, app):
        """Add the /metrics endpoint to the app."""
        # Check for endpoint conflicts
        if self.metrics_endpoint in [route.rule for route in app.routes]:
            raise RuntimeError(
                f"Metrics endpoint '{self.metrics_endpoint}' overlaps "
                "with existing routes"
            )

        def metrics_handler():
            """Handler for Prometheus metrics endpoint."""
            from pypiserver.bottle_wrapper import response

            try:
                # Update repository counts before serving metrics
                self._update_repository_stats()

                # Generate and return metrics
                metrics_bytes, content_type = self.collector.generate_metrics()

                response.content_type = content_type
                return metrics_bytes
            except Exception as e:
                response.status = 500
                response.content_type = "text/plain"
                return f"Error generating metrics: {str(e)}\n"

        app.route(self.metrics_endpoint, "GET", metrics_handler)


    def _update_repository_stats(self):
        """
        Update package and project counts from the backend.

        This method accesses the backend through self.config.backend
        to retrieve current package statistics.
        """
        if not self.config or not self.config.backend:
            return

        try:
            # Get total package count from backend
            package_count = len(list(self.config.backend.get_all_packages()))

            # Count unique projects
            projects = set()
            for pkg in self.config.backend.get_all_packages():
                projects.add(pkg.pkgname)
            project_count = len(projects)

            # Update metrics collector
            self.collector.update_package_counts(
                package_count=package_count,
                project_count=project_count
            )
        except AttributeError as e:
            # Handle cases where backend doesn't have expected methods
            # This allows the plugin to work even if backend interface changes
            pass
        except Exception as e:
            # Log but don't fail - metrics collection shouldn't break the server
            import logging
            logging.getLogger(__name__).warning(
                f"Failed to update repository stats: {e}"
            )

    def apply(self, callback, route):
        """
        Apply the plugin to a route (Bottle plugin API).

        This method is called for each route. We don't need to wrap
        individual routes since we use hooks for metrics collection.
        """
        return callback

    def close(self):
        """Clean up when plugin is uninstalled."""
        pass