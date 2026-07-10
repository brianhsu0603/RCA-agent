"""Central logging setup, shared by the API process, the Celery worker, and
one-off scripts (seed, eval). Call setup_logging() once at process start;
every module then just does `logger = logging.getLogger(__name__)`.
"""

import logging
import sys

from app.config import settings

_configured = False


def setup_logging() -> None:
    global _configured
    if _configured:
        return

    level = getattr(logging, settings.log_level.upper(), logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S%z",
        )
    )

    root = logging.getLogger()
    root.setLevel(level)
    root.handlers = [handler]

    # Quiet third-party request-noise loggers unless the app itself is at DEBUG.
    for noisy_logger in ("httpx", "httpcore"):
        logging.getLogger(noisy_logger).setLevel(max(level, logging.WARNING))

    _configured = True
