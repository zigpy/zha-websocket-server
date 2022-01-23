"""Button platform for zhawss."""
from __future__ import annotations

import abc
import functools
from typing import TYPE_CHECKING, Any, Final, Type, Union

from zhaws.server.platforms import PlatformEntity
from zhaws.server.platforms.registries import PLATFORM_ENTITIES, Platform
from zhaws.server.zigbee.cluster.const import CLUSTER_HANDLER_IDENTIFY

if TYPE_CHECKING:
    from zhaws.server.zigbee.cluster import ClusterHandler
    from zhaws.server.zigbee.device import Device
    from zhaws.server.zigbee.endpoint import Endpoint

MULTI_MATCH = functools.partial(PLATFORM_ENTITIES.multipass_match, Platform.BUTTON)
DEFAULT_DURATION: Final[int] = 5  # seconds


class Button(PlatformEntity):
    """Button platform entity."""

    _command_name: str
    PLATFORM = Platform.BUTTON

    def __init__(
        self,
        unique_id: str,
        cluster_handlers: list[ClusterHandler],
        endpoint: Endpoint,
        device: Device,
    ):
        """Initialize button."""
        super().__init__(unique_id, cluster_handlers, endpoint, device)
        self._cluster_handler: ClusterHandler = cluster_handlers[0]

    @abc.abstractmethod
    def get_args(self) -> list[Any]:
        """Return the arguments to use in the command."""

    def get_state(self) -> dict:
        """Return the arguments to use in the command."""

    async def async_press(self) -> None:
        """Send out a update command."""
        command = getattr(self._cluster_handler, self._command_name)
        arguments = self.get_args()
        await command(*arguments)

    def to_json(self) -> dict:
        """Return a JSON representation of the button."""
        json = super().to_json()
        json["command"] = self._command_name
        return json


@MULTI_MATCH(cluster_handler_names=CLUSTER_HANDLER_IDENTIFY)
class IdentifyButton(Button):
    """Identify button platform entity."""

    _command_name = "identify"

    @classmethod
    def create_platform_entity(
        cls: Type[IdentifyButton],
        unique_id: str,
        cluster_handlers: list[ClusterHandler],
        endpoint: Endpoint,
        device: Device,
        **kwargs: Any,
    ) -> Union[PlatformEntity, None]:
        """Entity Factory.
        Return a platform entity if it is a supported configuration, otherwise return None
        """
        if PLATFORM_ENTITIES.prevent_entity_creation(
            Platform.BUTTON, device.ieee, CLUSTER_HANDLER_IDENTIFY
        ):
            return None
        return cls(unique_id, cluster_handlers, endpoint, device, **kwargs)

    def get_args(self) -> list[Any]:
        """Return the arguments to use in the command."""

        return [DEFAULT_DURATION]
