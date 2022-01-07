"""Switch platform for zhawss."""

import functools
from typing import Any, List

from zigpy.zcl.foundation import Status

from zhawss.platforms import PlatformEntity
from zhawss.platforms.registries import PLATFORM_ENTITIES, Platform
from zhawss.zigbee.cluster.const import CLUSTER_HANDLER_ON_OFF
from zhawss.zigbee.cluster.general import OnOffClusterHandler
from zhawss.zigbee.cluster.types import ClusterHandlerType
from zhawss.zigbee.types import DeviceType, EndpointType

STRICT_MATCH = functools.partial(PLATFORM_ENTITIES.strict_match, Platform.SWITCH)


class BaseSwitch(PlatformEntity):
    """Common base class for zhawss switches."""

    PLATFORM = Platform.SWITCH

    def __init__(
        self,
        unique_id: str,
        cluster_handlers: List[ClusterHandlerType],
        endpoint: EndpointType,
        device: DeviceType,
    ):
        """Initialize the switch."""
        self._on_off_cluster_handler: OnOffClusterHandler = None
        self._state = None
        super().__init__(unique_id, cluster_handlers, endpoint, device)

    @property
    def is_on(self) -> bool:
        """Return if the switch is on based on the statemachine."""
        if self._state is None:
            return False
        return self._state

    async def async_turn_on(self, **kwargs) -> None:
        """Turn the entity on."""
        result = await self._on_off_channel.on()
        if not isinstance(result, list) or result[1] is not Status.SUCCESS:
            return
        self._state = True
        self.send_state_changed_event()

    async def async_turn_off(self, **kwargs) -> None:
        """Turn the entity off."""
        result = await self._on_off_channel.off()
        if not isinstance(result, list) or result[1] is not Status.SUCCESS:
            return
        self._state = False
        self.send_state_changed_event()


@STRICT_MATCH(cluster_handler_names=CLUSTER_HANDLER_ON_OFF)
class Switch(BaseSwitch):
    def __init__(
        self,
        unique_id: str,
        cluster_handlers: List[ClusterHandlerType],
        endpoint: EndpointType,
        device: DeviceType,
    ):
        """Initialize the switch."""
        super().__init__(unique_id, cluster_handlers, endpoint, device)
        self._on_off_cluster_handler: OnOffClusterHandler = self.cluster_handlers.get(
            CLUSTER_HANDLER_ON_OFF
        )
        self._state: bool = self._on_off_cluster_handler.cluster.get("on_off")
        self._on_off_cluster_handler.add_listener(self)

    def cluster_handler_attribute_updated(
        self, attr_id: int, attr_name: str, value: Any
    ):
        """Handle state update from cluster handler."""
        self._state = bool(value)
        self.send_state_changed_event()

    async def async_update(self) -> None:
        """Attempt to retrieve on off state from the switch."""
        await super().async_update()
        if self._on_off_cluster_handler:
            state = await self._on_off_cluster_handler.get_attribute_value("on_off")
            if state is not None:
                self._state = state
                self.send_state_changed_event()
