"""Button platform for zhawss."""

import abc
import functools
from typing import Any, Awaitable, Final, List, Union

from zhaws.server.platforms import PlatformEntity
from zhaws.server.platforms.registries import PLATFORM_ENTITIES, Platform
from zhaws.server.zigbee.cluster.const import CLUSTER_HANDLER_IDENTIFY
from zhaws.server.zigbee.cluster.types import ClusterHandlerType
from zhaws.server.zigbee.types import DeviceType, EndpointType

MULTI_MATCH = functools.partial(PLATFORM_ENTITIES.multipass_match, Platform.BUTTON)
DEFAULT_DURATION: Final[int] = 5  # seconds


class Button(PlatformEntity):
    """Button platform entity."""

    _command_name: str = None
    PLATFORM = Platform.BUTTON

    def __init__(
        self,
        unique_id: str,
        cluster_handlers: List[ClusterHandlerType],
        endpoint: EndpointType,
        device: DeviceType,
    ):
        """Initialize button."""
        super().__init__(unique_id, cluster_handlers, endpoint, device)
        self._cluster_handler: ClusterHandlerType = cluster_handlers[0]

    @abc.abstractmethod
    def get_args(self) -> list[Any]:
        """Return the arguments to use in the command."""

    async def async_press(self) -> Awaitable[None]:
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
        cls,
        unique_id: str,
        cluster_handlers: List[ClusterHandlerType],
        endpoint: EndpointType,
        device: DeviceType,
        **kwargs,
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
