"""Platform module for zhawss."""
from __future__ import annotations

import abc
import asyncio
import logging
from typing import TYPE_CHECKING, Any, Type, Union

from zhaws.server.const import EVENT, EVENT_TYPE, EventTypes, PlatformEntityEvents
from zhaws.server.platforms.registries import Platform

if TYPE_CHECKING:
    from zhaws.server.zigbee.cluster import ClusterHandler
    from zhaws.server.zigbee.device import Device
    from zhaws.server.zigbee.endpoint import Endpoint

from zhaws.server.util import LogMixin

_LOGGER = logging.getLogger(__name__)


class PlatformEntity(LogMixin):
    """Class that represents an entity for a device platform."""

    PLATFORM: str = Platform.UNKNOWN
    unique_id_suffix: Union[str, None] = None

    def __init_subclass__(
        cls: Type[PlatformEntity], id_suffix: Union[str, None] = None, **kwargs: Any
    ):
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
        cluster_handlers: list[ClusterHandler],
        endpoint: Endpoint,
        device: Device,
    ):
        """Initialize the platform entity."""
        self._unique_id: str = unique_id
        ieeetail = "".join([f"{o:02x}" for o in device.ieee[:4]])
        ch_names = ", ".join(sorted(ch.name for ch in cluster_handlers))
        self._name: str = f"{device.name} {ieeetail} {ch_names}"
        if self.unique_id_suffix:
            self._name += f" {self.unique_id_suffix}"
            self._unique_id += f"-{self.unique_id_suffix}"
        self._cluster_handlers: list[ClusterHandler] = cluster_handlers
        self.cluster_handlers: dict[str, ClusterHandler] = {}
        for cluster_handler in cluster_handlers:
            self.cluster_handlers[cluster_handler.name] = cluster_handler
        self._device: Device = device
        self._endpoint = endpoint
        self._device.platform_entities[self.unique_id] = self

    @classmethod
    def create_platform_entity(
        cls: Type[PlatformEntity],
        unique_id: str,
        cluster_handlers: list[ClusterHandler],
        endpoint: Endpoint,
        device: Device,
        **kwargs: Any,
    ) -> Union[PlatformEntity, None]:
        """Entity Factory.
        Return a platform entity if it is a supported configuration, otherwise return None
        """
        return cls(unique_id, cluster_handlers, endpoint, device, **kwargs)

    @property
    def device(self) -> Device:
        """Return the device."""
        return self._device

    @property
    def endpoint(self) -> Endpoint:
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

    @property
    def name(self) -> str:
        """Return the name of the platform entity."""
        return self._name

    def send_event(self, signal: dict[str, Any]) -> None:
        """Broadcast an event from this platform entity."""
        signal["platform_entity"] = {
            "name": self._name,
            "unique_id": self._unique_id,
            "platform": self.PLATFORM,
        }
        signal["endpoint"] = {
            "id": self._endpoint.id,
        }
        _LOGGER.info("Sending event from platform entity: %s", signal)
        self.device.send_event(signal)

    @abc.abstractmethod
    def get_state(self) -> Union[float, bool, int, str, dict, None]:
        """Return the arguments to use in the command."""

    def send_state_changed_event(self) -> None:
        """Send the state of this platform entity."""
        self.send_event(
            {
                "state": self.get_state(),
                EVENT: PlatformEntityEvents.PLATFORM_ENTITY_STATE_CHANGED,
                EVENT_TYPE: EventTypes.PLATFORM_ENTITY_EVENT,
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
            "platform": self.PLATFORM,
            "class_name": self.__class__.__name__,
            "state": self.get_state(),
        }

    async def async_update(self) -> None:
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

    def log(self, level: int, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log a message."""
        msg = f"%s: {msg}"
        args = (self.unique_id,) + args
        _LOGGER.log(level, msg, *args, **kwargs)
