"""Platform module for zhawss."""


from typing import List, Union

from zhawss.platforms.registries import Platform
from zhawss.platforms.types import PlatformEntityType
from zhawss.zigbee.cluster.types import ClusterHandlerType
from zhawss.zigbee.types import DeviceType, EndpointType


class PlatformEntity:
    """Class that represents an entity for a device platform."""

    PLATFORM: Platform = Platform.UNKNOWN

    def __init_subclass__(cls, id_suffix: Union[str, None] = None, **kwargs) -> None:
        """Initialize subclass.
        :param id_suffix: suffix to add to the unique_id of the entity. Used for multi
                          entities using the same channel/cluster id for the entity.
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
        self._cluster_handlers: List[ClusterHandlerType] = cluster_handlers
        self._unique_id: str = unique_id
        ieeetail = "".join([f"{o:02x}" for o in device.ieee[:4]])
        ch_names = ", ".join(sorted(ch.name for ch in cluster_handlers))
        self._name: str = f"{device.name} {ieeetail} {ch_names}"
        if self.unique_id_suffix:
            self._name += f" {self.unique_id_suffix}"
        self.cluster_handlers: dict[str, ClusterHandlerType] = {}
        for cluster_handler in cluster_handlers:
            self.cluster_handlers[cluster_handler.name] = cluster_handler
        self._device: DeviceType = device
        self._endpoint = endpoint

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

    def to_json(self) -> dict:
        """Return a JSON representation of the platform entity."""
        return {
            "name": self._name,
            "unique_id": self._unique_id,
            "cluster_handlers": [
                ch.to_json() for ch in self._cluster_handlers.values()
            ],
            "device_ieee": str(self._device.ieee),
            "endpoint_id": self._endpoint.id,
            "platform": self.PLATFORM.name,
        }
