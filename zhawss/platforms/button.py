"""Button platform for zhawss."""

import functools
from typing import List, Union

from zhawss.platforms import PlatformEntity
from zhawss.platforms.registries import PLATFORM_ENTITIES, Platform
from zhawss.zigbee.cluster.const import CLUSTER_HANDLER_IDENTIFY
from zhawss.zigbee.cluster.types import ClusterHandlerType
from zhawss.zigbee.types import DeviceType, EndpointType

MULTI_MATCH = functools.partial(PLATFORM_ENTITIES.multipass_match, Platform.BUTTON)


class Button(PlatformEntity):
    """Button platform entity."""

    PLATFORM = Platform.BUTTON


@MULTI_MATCH(cluster_handler_names=CLUSTER_HANDLER_IDENTIFY)
class IdentifyButton(Button):
    """Identify button platform entity."""

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

    def to_json(self) -> dict:
        """Return a JSON representation of the button."""
        json = super().to_json()
        json["command"] = "identify"
        return json
