"""Entry point for the worker: `dramatiq app.worker.tasks`."""

import logging

import dramatiq

# Importing the broker module sets the broker before any actor is declared.
from app.worker import broker  # noqa: F401

logger = logging.getLogger(__name__)


@dramatiq.actor
def ping() -> None:
    """Placeholder actor so the worker has something to load. AI jobs arrive in Step 6."""
    logger.info("pong")
