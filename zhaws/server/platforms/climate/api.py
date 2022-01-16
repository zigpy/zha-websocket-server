"""WS api for the climate platform entity."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

import voluptuous as vol

from zhaws.backports.enum import StrEnum
from zhaws.server.platforms.api import (
    execute_platform_entity_command,
    platform_entity_command_schema,
)
from zhaws.server.platforms.climate import (
    ATTR_FAN_MODE,
    ATTR_HVAC_MODE,
    ATTR_TARGET_TEMP_HIGH,
    ATTR_TARGET_TEMP_LOW,
    ATTR_TEMPERATURE,
)
from zhaws.server.websocket.api import decorators, register_api_command

if TYPE_CHECKING:
    from zhaws.server.websocket.client import Client
    from zhaws.server.websocket.server import Server

# All activity disabled / Device is off/standby
HVAC_MODE_OFF = "off"

# Heating
HVAC_MODE_HEAT = "heat"

# Cooling
HVAC_MODE_COOL = "cool"

# The device supports heating/cooling to a range
HVAC_MODE_HEAT_COOL = "heat_cool"

# The temperature is set based on a schedule, learned behavior, AI or some
# other related mechanism. User is not able to adjust the temperature
HVAC_MODE_AUTO = "auto"

# Device is in Dry/Humidity mode
HVAC_MODE_DRY = "dry"

# Only the fan is on, not fan and another mode like cool
HVAC_MODE_FAN_ONLY = "fan_only"

HVAC_MODES = [
    HVAC_MODE_OFF,
    HVAC_MODE_HEAT,
    HVAC_MODE_COOL,
    HVAC_MODE_HEAT_COOL,
    HVAC_MODE_AUTO,
    HVAC_MODE_DRY,
    HVAC_MODE_FAN_ONLY,
]

ATTR_PRESET_MODE = "preset_mode"


class ClimateCommands(StrEnum):
    """Climate commands."""

    SET_FAN_MODE = "climate_set_fan_mode"
    SET_HVAC_MODE = "climate_set_hvac_mode"
    SET_PRESET_MODE = "climate_set_preset_mode"
    SET_TEMPERATURE = "climate_set_temperature"


@decorators.websocket_command(
    platform_entity_command_schema(
        ClimateCommands.SET_FAN_MODE,
        {
            vol.Required(ATTR_FAN_MODE): str,
        },
    )
)
@decorators.async_response
async def set_fan_mode(server: Server, client: Client, message: dict[str, Any]) -> None:
    """Set the fan mode for the climate platform entity."""
    await execute_platform_entity_command(server, client, message, "async_set_fan_mode")


@decorators.websocket_command(
    platform_entity_command_schema(
        ClimateCommands.SET_HVAC_MODE,
        {
            vol.Required(ATTR_HVAC_MODE): vol.In(HVAC_MODES),
        },
    )
)
@decorators.async_response
async def set_hvac_mode(
    server: Server, client: Client, message: dict[str, Any]
) -> None:
    """Set the hvac mode for the climate platform entity."""
    await execute_platform_entity_command(
        server, client, message, "async_set_hvac_mode"
    )


@decorators.websocket_command(
    platform_entity_command_schema(
        ClimateCommands.SET_PRESET_MODE,
        {
            vol.Required(ATTR_PRESET_MODE): str,
        },
    )
)
@decorators.async_response
async def set_preset_mode(
    server: Server, client: Client, message: dict[str, Any]
) -> None:
    """Set the preset mode for the climate platform entity."""
    await execute_platform_entity_command(
        server, client, message, "async_set_preset_mode"
    )


@decorators.websocket_command(
    platform_entity_command_schema(
        ClimateCommands.SET_TEMPERATURE,
        {
            vol.Exclusive(ATTR_TEMPERATURE, "temperature"): vol.Coerce(float),
            vol.Inclusive(ATTR_TARGET_TEMP_HIGH, "temperature"): vol.Coerce(float),
            vol.Inclusive(ATTR_TARGET_TEMP_LOW, "temperature"): vol.Coerce(float),
            vol.Optional(ATTR_HVAC_MODE): vol.In(HVAC_MODES),
        },
    )
)
@decorators.async_response
async def set_temperature(
    server: Server, client: Client, message: dict[str, Any]
) -> None:
    """Set the temperature and hvac mode for the climate platform entity."""
    await execute_platform_entity_command(
        server, client, message, "async_set_temperature"
    )


def load_api(server: Server) -> None:
    """Load the api command handlers."""
    register_api_command(server, set_fan_mode)
    register_api_command(server, set_hvac_mode)
    register_api_command(server, set_preset_mode)
    register_api_command(server, set_temperature)
