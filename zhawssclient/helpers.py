"""Helper classes for zhawssclient."""

from typing import Awaitable

from zhawssclient.client import Client
from zhawssclient.model.commands import (
    LightTurnOffCommand,
    LightTurnOnCommand,
    SwitchTurnOffCommand,
    SwitchTurnOnCommand,
)
from zhawssclient.model.types import ControllerType


class LightHelper:
    """Helper to issue light commands."""

    CONTROLLER_ATTRIBUTE = "lights"

    def __init__(self, client: Client):
        """Initialize the light helper."""
        self._client: Client = client

    async def turn_on(
        self,
        light_platform_entity,
        brightness=None,
        transition=None,
        flash=None,
        effect=None,
        hs_color=None,
        color_temp=None,
    ) -> Awaitable[None]:
        """Turn on a light."""
        if light_platform_entity is None or light_platform_entity.platform != "LIGHT":
            raise ValueError(
                "light_platform_entity must be provided and it must be a light platform entity"
            )

        command = LightTurnOnCommand(
            ieee=light_platform_entity.device_ieee,
            unique_id=light_platform_entity.unique_id,
            brightness=brightness,
            transition=transition,
            flash=flash,
            effect=effect,
            hs_color=hs_color,
            color_temp=color_temp,
        )
        return await self._client.async_send_command(command.dict(exclude_none=True))

    async def turn_off(
        self, light_platform_entity, transition=None, flash=None
    ) -> Awaitable[None]:
        """Turn off a light."""
        if light_platform_entity is None or light_platform_entity.platform != "LIGHT":
            raise ValueError(
                "light_platform_entity must be provided and it must be a light platform entity"
            )

        command = LightTurnOffCommand(
            ieee=light_platform_entity.device_ieee,
            unique_id=light_platform_entity.unique_id,
            transition=transition,
            flash=flash,
        )
        return await self._client.async_send_command(command.dict(exclude_none=True))


class SwitchHelper:
    """Helper to issue switch commands."""

    CONTROLLER_ATTRIBUTE = "switches"

    def __init__(self, client: Client):
        """Initialize the switch helper."""
        self._client: Client = client

    async def turn_on(self, switch_platform_entity) -> Awaitable[None]:
        """Turn on a switch."""
        if (
            switch_platform_entity is None
            or switch_platform_entity.platform != "SWITCH"
        ):
            raise ValueError(
                "switch_platform_entity must be provided and it must be a switch platform entity"
            )

        command = SwitchTurnOnCommand(
            ieee=switch_platform_entity.device_ieee,
            unique_id=switch_platform_entity.unique_id,
        )
        return await self._client.async_send_command(command.dict(exclude_none=True))

    async def turn_off(self, switch_platform_entity) -> Awaitable[None]:
        """Turn off a switch."""
        if (
            switch_platform_entity is None
            or switch_platform_entity.platform != "SWITCH"
        ):
            raise ValueError(
                "switch_platform_entity must be provided and it must be a switch platform entity"
            )

        command = SwitchTurnOffCommand(
            ieee=switch_platform_entity.device_ieee,
            unique_id=switch_platform_entity.unique_id,
        )
        return await self._client.async_send_command(command.dict(exclude_none=True))


def attach_platform_entity_helpers(controller: ControllerType, client: Client) -> None:
    """Attach helper methods to the controller."""
    setattr(controller, LightHelper.CONTROLLER_ATTRIBUTE, LightHelper(client))
    setattr(controller, SwitchHelper.CONTROLLER_ATTRIBUTE, SwitchHelper(client))
