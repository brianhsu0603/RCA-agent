"""Sentry error tracking, shared by the API process and the Celery worker.

No-ops entirely if SENTRY_DSN isn't set, so this is safe to call unconditionally
from every entrypoint. Wired to the stdlib `logging` integration so the ERROR/
CRITICAL logs already emitted throughout the app (see app/logging_config.py)
are reported as Sentry events without any extra instrumentation.
"""

import logging

import sentry_sdk
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration

from app.config import settings

_configured = False


def init_sentry() -> None:
    global _configured
    if _configured or not settings.sentry_dsn:
        return

    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.sentry_environment,
        traces_sample_rate=settings.sentry_traces_sample_rate,
        integrations=[
            StarletteIntegration(),
            FastApiIntegration(),
            CeleryIntegration(),
            LoggingIntegration(level=logging.INFO, event_level=logging.ERROR),
        ],
    )
    _configured = True
