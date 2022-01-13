"""WS api for the lock platform entity."""

from typing import Any, Awaitable

from backports.strenum.strenum import StrEnum
import voluptuous as vol

from zhawss.platforms.api import (
    execute_platform_entity_command,
    platform_entity_command_schema,
)
from zhawss.websocket.api import decorators, register_api_command
from zhawss.websocket.types import ClientType, ServerType


class LockCommands(StrEnum):
    """Lock commands."""

    LOCK = "lock_lock"
    UNLOCK = "lock_unlock"
    SET_USER_LOCK_CODE = "lock_set_user_lock_code"
    ENABLE_USER_LOCK_CODE = "lock_enable_user_lock_code"
    DISABLE_USER_LOCK_CODE = "lock_disable_user_lock_code"
    CLEAR_USER_LOCK_CODE = "lock_clear_user_lock_code"


@decorators.async_response
@decorators.websocket_command(platform_entity_command_schema(LockCommands.LOCK))
async def lock(
    server: ServerType, client: ClientType, message: dict[str, Any]
) -> Awaitable[None]:
    """Lock the lock."""
    await execute_platform_entity_command(server, client, message, "async_lock")


@decorators.async_response
@decorators.websocket_command(platform_entity_command_schema(LockCommands.UNLOCK))
async def unlock(
    server: ServerType, client: ClientType, message: dict[str, Any]
) -> Awaitable[None]:
    """Unlock the lock."""
    await execute_platform_entity_command(server, client, message, "async_unlock")


@decorators.async_response
@decorators.websocket_command(
    platform_entity_command_schema(
        LockCommands.SET_USER_LOCK_CODE,
        {
            vol.Required("code_slot"): vol.Coerce(int),
            vol.Required("user_code"): str,
        },
    )
)
async def set_user_lock_code(
    server: ServerType, client: ClientType, message: dict[str, Any]
) -> Awaitable[None]:
    """Set a user lock code in the specified slot for the lock."""
    await execute_platform_entity_command(
        server, client, message, "async_set_user_lock_code"
    )


@decorators.async_response
@decorators.websocket_command(
    platform_entity_command_schema(
        LockCommands.ENABLE_USER_LOCK_CODE,
        {
            vol.Required("code_slot"): vol.Coerce(int),
        },
    )
)
async def enable_user_lock_code(
    server: ServerType, client: ClientType, message: dict[str, Any]
) -> Awaitable[None]:
    """Enable a user lock code for the lock."""
    await execute_platform_entity_command(
        server, client, message, "async_enable_user_lock_code"
    )


@decorators.async_response
@decorators.websocket_command(
    platform_entity_command_schema(
        LockCommands.DISABLE_USER_LOCK_CODE,
        {
            vol.Required("code_slot"): vol.Coerce(int),
        },
    )
)
async def disable_user_lock_code(
    server: ServerType, client: ClientType, message: dict[str, Any]
) -> Awaitable[None]:
    """Disable a user lock code for the lock."""
    await execute_platform_entity_command(
        server, client, message, "async_disable_user_lock_code"
    )


@decorators.async_response
@decorators.websocket_command(
    platform_entity_command_schema(
        LockCommands.CLEAR_USER_LOCK_CODE,
        {
            vol.Required("code_slot"): vol.Coerce(int),
        },
    )
)
async def clear_user_lock_code(
    server: ServerType, client: ClientType, message: dict[str, Any]
) -> Awaitable[None]:
    """Clear a user lock code for the lock."""
    await execute_platform_entity_command(
        server, client, message, "async_clear_user_lock_code"
    )


def load_api(server: ServerType) -> None:
    """Load the api command handlers."""
    register_api_command(server, lock)
    register_api_command(server, unlock)
    register_api_command(server, set_user_lock_code)
    register_api_command(server, enable_user_lock_code)
    register_api_command(server, disable_user_lock_code)
    register_api_command(server, clear_user_lock_code)
