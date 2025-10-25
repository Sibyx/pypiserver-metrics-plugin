"""
Debug entry point for the metrics plugin.

This module allows you to run pypiserver with the metrics plugin for testing/debugging:

    python -m pypiserver_metrics_plugin [OPTIONS]

Examples:
    # Basic usage with default package directory
    python -m pypiserver_metrics_plugin

    # Specify custom package directory
    python -m pypiserver_metrics_plugin --packages ./my-packages

    # Run on different port with custom metrics endpoint
    METRICS_ENDPOINT=/custom-metrics python -m pypiserver_metrics_plugin --port 9090

    # Enable verbose logging
    python -m pypiserver_metrics_plugin -v
"""

import argparse
import logging
import os
import sys
from pathlib import Path

import pypiserver
from pypiserver_metrics_plugin import MetricsPlugin


def main():
    """Run pypiserver with metrics plugin for debugging/testing."""
    parser = argparse.ArgumentParser(
        description="Run pypiserver with Prometheus metrics plugin (debug mode)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Environment Variables:
  METRICS_ENDPOINT    Path for metrics endpoint (default: /metrics)

Examples:
  python -m pypiserver_metrics_plugin
  python -m pypiserver_metrics_plugin --packages ./my-packages
  METRICS_ENDPOINT=/custom-metrics python -m pypiserver_metrics_plugin
        """,
    )

    parser.add_argument(
        "--packages",
        "-p",
        default="./data/packages",
        help="Package directory (default: ./data/packages)",
    )
    parser.add_argument(
        "--port",
        "-P",
        type=int,
        default=8080,
        help="Port to listen on (default: 8080)",
    )
    parser.add_argument(
        "--host",
        "-H",
        default="0.0.0.0",
        help="Host to bind to (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logger = logging.getLogger(__name__)

    # Ensure package directory exists
    pkg_dir = Path(args.packages)
    if not pkg_dir.exists():
        logger.info(f"Creating package directory: {pkg_dir}")
        pkg_dir.mkdir(parents=True, exist_ok=True)
    else:
        logger.info(f"Using package directory: {pkg_dir}")

    # Get metrics endpoint from env or use default
    metrics_endpoint = os.getenv("METRICS_ENDPOINT", "/metrics")

    # Create pypiserver app
    logger.info("Creating pypiserver application...")
    app = pypiserver.app(roots=[str(pkg_dir)])

    # Install metrics plugin
    logger.info(f"Installing metrics plugin (endpoint: {metrics_endpoint})...")
    try:
        app.install(MetricsPlugin(metrics_endpoint=metrics_endpoint))
        logger.info("✓ Metrics plugin installed successfully")
    except Exception as e:
        logger.error(f"✗ Failed to install metrics plugin: {e}")
        sys.exit(1)

    # Print startup info
    print("\n" + "=" * 60)
    print(f"PyPI Server with Metrics Plugin")
    print("=" * 60)
    print(f"  Server URL:     http://{args.host}:{args.port}/")
    print(f"  Metrics URL:    http://{args.host}:{args.port}{metrics_endpoint}")
    print(f"  Package dir:    {pkg_dir.absolute()}")
    print("=" * 60)
    print("\nPress Ctrl+C to stop the server\n")

    # Run server
    try:
        app.run(host=args.host, port=args.port, debug=args.verbose)
    except KeyboardInterrupt:
        print("\n\nShutting down server...")
        sys.exit(0)


if __name__ == "__main__":
    main()