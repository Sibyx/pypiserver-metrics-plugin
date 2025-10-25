"""WSGI application"""
import os
import pypiserver
from pypiserver_metrics_plugin import MetricsPlugin

# Create pypiserver app with env configuration
app = pypiserver.app(
    roots=[os.getenv('PACKAGES_DIR', '/data/packages')],
    disable_fallback=True,
    fallback_url=os.getenv('FALLBACK_URL', 'https://pypi.org/simple')
)

# Install metrics plugin
app.install(MetricsPlugin(
    metrics_endpoint=os.getenv('METRICS_ENDPOINT', '/metrics')
))

application = app