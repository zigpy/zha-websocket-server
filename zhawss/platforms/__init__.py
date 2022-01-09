"""Platform module for zhawss."""


import abc
import asyncio
import logging
from typing import Any, Awaitable, Dict, List, Union

from zhawss.platforms.registries import Platform
from zhawss.platforms.types import PlatformEntityType
from zhawss.util import LogMixin
from zhawss.zigbee.cluster.types import ClusterHandlerType
from zhawss.zigbee.types import DeviceType, EndpointType

_LOGGER = logging.getLogger(__name__)


class PlatformEntity(LogMixin):
    """Class that represents an entity for a device platform."""

    PLATFORM: Platform = Platform.UNKNOWN
    unique_id_suffix: Union[str, None] = None

    def __init_subclass__(cls, id_suffix: Union[str, None] = None, **kwargs) -> None:
        """Initialize subclass.
        :param id_suffix: suffix to add to the unique_id of the entity. Used for multi
                          entities using the same cluster handler/cluster id for the entity.
        """
        super().__init_subclass__(**kwargs)
        if id_suffix:
            cls.unique_id_suffix = id_suffix

    def __init__(
        self,
        unique_id: str,
        cluster_handlers: List[ClusterHandlerType],
        endpoint: EndpointType,
        device: DeviceType,
    ):
        """Initialize the platform entity."""
        self._unique_id: str = unique_id
        ieeetail = "".join([f"{o:02x}" for o in device.ieee[:4]])
        ch_names = ", ".join(sorted(ch.name for ch in cluster_handlers))
        self._name: str = f"{device.name} {ieeetail} {ch_names}"
        if self.unique_id_suffix:
            self._name += f" {self.unique_id_suffix}"
        self._cluster_handlers: List[ClusterHandlerType] = cluster_handlers
        self.cluster_handlers: dict[str, ClusterHandlerType] = {}
        for cluster_handler in cluster_handlers:
            self.cluster_handlers[cluster_handler.name] = cluster_handler
        self._device: DeviceType = device
        self._endpoint = endpoint
        self._device.platform_entities[self.unique_id] = self

    @classmethod
    def create_platform_entity(
        cls,
        unique_id: str,
        cluster_handlers: List[ClusterHandlerType],
        endpoint: EndpointType,
        device: DeviceType,
        **kwargs,
    ) -> Union[PlatformEntityType, None]:
        """Entity Factory.
        Return a platform entity if it is a supported configuration, otherwise return None
        """
        return cls(unique_id, cluster_handlers, endpoint, device, **kwargs)

    @property
    def device(self):
        """Return the device."""
        return self._device

    @property
    def endpoint(self) -> EndpointType:
        """Return the endpoint."""
        return self._endpoint

    @property
    def unique_id(self) -> str:
        """Return the unique id."""
        return self._unique_id

    @property
    def should_poll(self) -> bool:
        """Return True if we need to poll for state changes."""
        return False

    @property
    def available(self) -> bool:
        """Return true if the device this entity belongs to is available."""
        return self.device.available

    def send_event(self, signal: dict[str, Any]) -> None:
        """Broadcast an event from this platform entity."""
        signal["platform_entity"] = {
            "name": self._name,
            "unique_id": self._unique_id,
            "platform": self.PLATFORM.name,
        }
        signal["endpoint"] = {
            "id": self._endpoint.id,
        }
        _LOGGER.info("Sending event from platform entity: %s", signal)
        self.device.send_event({"data": signal})

    @abc.abstractmethod
    def get_state(self) -> Union[str, Dict, None]:
        """Return the arguments to use in the command."""

    def send_state_changed_event(self) -> None:
        """Send the state of this platform entity."""
        self.send_event(
            {
                "state": self.get_state(),
                "event": "platform_entity_state_changed",
                "event_type": "platform_entity_event",
            }
        )

    def to_json(self) -> dict:
        """Return a JSON representation of the platform entity."""
        return {
            "name": self._name,
            "unique_id": self._unique_id,
            "cluster_handlers": [ch.to_json() for ch in self._cluster_handlers],
            "device_ieee": str(self._device.ieee),
            "endpoint_id": self._endpoint.id,
            "platform": self.PLATFORM.name,
            "class_name": self.__class__.__name__,
        }

    async def async_update(self) -> Awaitable[None]:
        """Retrieve latest state."""
        tasks = [
            cluster_handler.async_update()
            for cluster_handler in self.cluster_handlers.values()
            if hasattr(cluster_handler, "async_update")
        ]
        if tasks:
            previous_state = self.get_state()
            await asyncio.gather(*tasks)
            state = self.get_state()
            if state != previous_state:
                self.send_state_changed_event()

    def log(self, level: int, msg: str, *args):
        """Log a message."""
        msg = f"%s: {msg}"
        args = (self.unique_id,) + args
        _LOGGER.log(level, msg, *args)
