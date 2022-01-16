"""WS api for the lock platform entity."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

import voluptuous as vol

from zhaws.backports.enum import StrEnum
from zhaws.server.platforms.api import (
    execute_platform_entity_command,
    platform_entity_command_schema,
)
from zhaws.server.websocket.api import decorators, register_api_command

if TYPE_CHECKING:
    from zhaws.server.websocket.client import Client
    from zhaws.server.websocket.server import Server


class LockCommands(StrEnum):
    """Lock commands."""

    LOCK = "lock_lock"
    UNLOCK = "lock_unlock"
    SET_USER_LOCK_CODE = "lock_set_user_lock_code"
    ENABLE_USER_LOCK_CODE = "lock_enable_user_lock_code"
    DISABLE_USER_LOCK_CODE = "lock_disable_user_lock_code"
    CLEAR_USER_LOCK_CODE = "lock_clear_user_lock_code"


@decorators.websocket_command(platform_entity_command_schema(LockCommands.LOCK))
@decorators.async_response
async def lock(server: Server, client: Client, message: dict[str, Any]) -> None:
    """Lock the lock."""
    await execute_platform_entity_command(server, client, message, "async_lock")


@decorators.websocket_command(platform_entity_command_schema(LockCommands.UNLOCK))
@decorators.async_response
async def unlock(server: Server, client: Client, message: dict[str, Any]) -> None:
    """Unlock the lock."""
    await execute_platform_entity_command(server, client, message, "async_unlock")


@decorators.websocket_command(
    platform_entity_command_schema(
        LockCommands.SET_USER_LOCK_CODE,
        {
            vol.Required("code_slot"): vol.Coerce(int),
            vol.Required("user_code"): str,
        },
    )
)
@decorators.async_response
async def set_user_lock_code(
    server: Server, client: Client, message: dict[str, Any]
) -> None:
    """Set a user lock code in the specified slot for the lock."""
    await execute_platform_entity_command(
        server, client, message, "async_set_user_lock_code"
    )


@decorators.websocket_command(
    platform_entity_command_schema(
        LockCommands.ENABLE_USER_LOCK_CODE,
        {
            vol.Required("code_slot"): vol.Coerce(int),
        },
    )
)
@decorators.async_response
async def enable_user_lock_code(
    server: Server, client: Client, message: dict[str, Any]
) -> None:
    """Enable a user lock code for the lock."""
    await execute_platform_entity_command(
        server, client, message, "async_enable_user_lock_code"
    )


@decorators.websocket_command(
    platform_entity_command_schema(
        LockCommands.DISABLE_USER_LOCK_CODE,
        {
            vol.Required("code_slot"): vol.Coerce(int),
        },
    )
)
@decorators.async_response
async def disable_user_lock_code(
    server: Server, client: Client, message: dict[str, Any]
) -> None:
    """Disable a user lock code for the lock."""
    await execute_platform_entity_command(
        server, client, message, "async_disable_user_lock_code"
    )


@decorators.websocket_command(
    platform_entity_command_schema(
        LockCommands.CLEAR_USER_LOCK_CODE,
        {
            vol.Required("code_slot"): vol.Coerce(int),
        },
    )
)
@decorators.async_response
async def clear_user_lock_code(
    server: Server, client: Client, message: dict[str, Any]
) -> None:
    """Clear a user lock code for the lock."""
    await execute_platform_entity_command(
        server, client, message, "async_clear_user_lock_code"
    )


def load_api(server: Server) -> None:
    """Load the api command handlers."""
    register_api_command(server, lock)
    register_api_command(server, unlock)
    register_api_command(server, set_user_lock_code)
    register_api_command(server, enable_user_lock_code)
    register_api_command(server, disable_user_lock_code)
    register_api_command(server, clear_user_lock_code)
