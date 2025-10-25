# pypiserver-metrics-plugin

Prometheus metrics for [pypiserver](https://github.com/pypiserver/pypiserver). Implemented as a Bottle plugin.

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Installation

```bash
pip install -e .
```

## Usage

```python
import pypiserver
from pypiserver_metrics_plugin import MetricsPlugin

app = pypiserver.app(roots=['./packages'])
app.install(MetricsPlugin())
app.run(host='0.0.0.0', port=8080)
```

Metrics available at: http://localhost:8080/metrics

### Docker

```bash
docker compose up -d
```

Environment variables:
- `PACKAGES_DIR` - Package storage directory (default: `/data/packages`)
- `FALLBACK_URL` - PyPI fallback URL (default: `https://pypi.org/simple`)
- `METRICS_ENDPOINT` - Metrics path (default: `/metrics`)

### Production (WSGI)

```python
# app.py
import pypiserver
from pypiserver_metrics_plugin import MetricsPlugin

app = pypiserver.app(roots=['./packages'])
app.install(MetricsPlugin())
```

```bash
gunicorn app:app --bind 0.0.0.0:8080 --workers 4
```

## Available Metrics

### HTTP Metrics
- `pypiserver_http_requests_total` - Total HTTP requests (labels: method, endpoint, status_code)
- `pypiserver_http_request_duration_seconds` - HTTP request duration histogram (labels: method, endpoint, status_code)

### Package Operation Metrics
- `pypiserver_package_downloads_total` - Total package downloads (labels: package_name, filename)
- `pypiserver_package_uploads_total` - Total successful package uploads (labels: package_name, user)
- `pypiserver_package_upload_failures_total` - Total failed package uploads (labels: reason)
- `pypiserver_package_removals_total` - Total package removals (labels: package_name, user)

### Repository State Metrics
- `pypiserver_packages_total` - Current number of package files
- `pypiserver_projects_total` - Current number of unique projects

### Search & Discovery Metrics
- `pypiserver_searches_total` - Total search operations (labels: search_type)
- `pypiserver_simple_index_requests_total` - Total PEP 503 simple index requests (labels: project_name)

### Authentication Metrics
- `pypiserver_auth_attempts_total` - Total authentication attempts (labels: action, result)

### Error Metrics
- `pypiserver_errors_total` - Total errors (labels: endpoint, error_type, status_code)

### System Info
- `pypiserver` - Server information (labels: version, backend_type, fallback_url)
- `pypiserver_uptime_seconds` - Server uptime in seconds

## Prometheus Setup

Add to your `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'pypiserver'
    static_configs:
      - targets: ['localhost:8080']
    metrics_path: '/metrics'
```

Useful queries:

```promql
# Request rate
rate(pypiserver_http_requests_total[5m])

# Download rate by package
rate(pypiserver_package_downloads_total[5m])

# P95 latency
histogram_quantile(0.95, rate(pypiserver_http_request_duration_seconds_bucket[5m]))
```

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest --cov=pypiserver_metrics_plugin

# Format code
black .
```

## License

MIT