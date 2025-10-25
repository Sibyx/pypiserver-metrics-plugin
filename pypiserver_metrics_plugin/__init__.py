"""
PyPI Server Metrics Plugin

A non-invasive Bottle plugin for collecting Prometheus metrics from pypiserver.

Usage:
    import pypiserver
    from pypiserver_metrics_plugin import MetricsPlugin

    app = pypiserver.app(roots=['./packages'])
    app.install(MetricsPlugin())
"""

from .plugin import MetricsPlugin
from .collector import MetricsCollector

__version__ = "0.1.0"
__all__ = ["MetricsPlugin", "MetricsCollector"]