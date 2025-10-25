FROM python:3.14-slim

# Set working directory
WORKDIR /app

# Copy requirements first for better layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy plugin source code
COPY pypiserver_metrics_plugin/ ./pypiserver_metrics_plugin/
COPY pyproject.toml .
COPY README.md .

# Install the plugin
RUN pip install --no-cache-dir -e .

# Install gunicorn for production WSGI server
RUN pip install --no-cache-dir gunicorn>=21.0

# Create directory for packages
RUN mkdir -p /data/packages

# Expose default port
EXPOSE 8080

# Volume for package storage
VOLUME ["/data/packages"]

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/').read()"

# Run with gunicorn
CMD ["gunicorn", "pypiserver_metrics_plugin.wsgi:application", "--bind", "0.0.0.0:8080", "--workers", "4", "--access-logfile", "-"]