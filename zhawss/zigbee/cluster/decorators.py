"""Decorators for zhawss."""
import asyncio
from functools import wraps
import itertools
from random import uniform

import zigpy.exceptions


def decorate_command(cluster_handler, command):
    """Wrap a cluster command to make it safe."""

    @wraps(command)
    async def wrapper(*args, **kwds):
        try:
            result = await command(*args, **kwds)
            cluster_handler.debug(
                "executed '%s' command with args: '%s' kwargs: '%s' result: %s",
                command.__name__,
                args,
                kwds,
                result,
            )
            return result

        except (zigpy.exceptions.ZigbeeException, asyncio.TimeoutError) as ex:
            cluster_handler.debug(
                "command failed: '%s' args: '%s' kwargs '%s' exception: '%s'",
                command.__name__,
                args,
                kwds,
                str(ex),
            )
            return ex

    return wrapper


def retryable_request(
    delays=(1, 5, 10, 15, 30, 60, 120, 180, 360, 600, 900, 1800), raise_=False
):
    """Make a method with ZCL requests retryable.
    This adds delays keyword argument to function.
    len(delays) is number of tries.
    raise_ if the final attempt should raise the exception.
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(cluster_handler, *args, **kwargs):

            exceptions = (zigpy.exceptions.ZigbeeException, asyncio.TimeoutError)
            try_count, errors = 1, []
            for delay in itertools.chain(delays, [None]):
                try:
                    return await func(cluster_handler, *args, **kwargs)
                except exceptions as ex:
                    errors.append(ex)
                    if delay:
                        delay = uniform(delay * 0.75, delay * 1.25)
                        cluster_handler.debug(
                            (
                                "%s: retryable request #%d failed: %s. "
                                "Retrying in %ss"
                            ),
                            func.__name__,
                            try_count,
                            ex,
                            round(delay, 1),
                        )
                        try_count += 1
                        await asyncio.sleep(delay)
                    else:
                        cluster_handler.warning(
                            "%s: all attempts have failed: %s", func.__name__, errors
                        )
                        if raise_:
                            raise

        return wrapper

    return decorator
