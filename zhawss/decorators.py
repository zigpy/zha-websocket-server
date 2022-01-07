"""Decorators for zhawss."""

import asyncio
import logging

_LOGGER = logging.getLogger(__name__)


def periodic(period):
    def scheduler(func):
        async def wrapper(*args, **kwargs):
            while True:
                try:
                    _LOGGER.info("executing periodic task %s", func.__name__)
                    await func(*args, **kwargs)
                except Exception:
                    _LOGGER.warning(
                        "Failed to poll using function %s", func.__name__, exc_info=True
                    )
                await asyncio.sleep(period)

        return wrapper

    return scheduler
