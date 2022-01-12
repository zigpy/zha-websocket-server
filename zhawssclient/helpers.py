"""Helper classes for zhawssclient."""

from typing import Awaitable

from zhawssclient.client import Client
from zhawssclient.model.commands import LightTurnOffCommand, LightTurnOnCommand


class LightHelper:
    """Helper to issue light commands."""

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
