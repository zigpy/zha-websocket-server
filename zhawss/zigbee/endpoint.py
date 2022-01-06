"""Representation of a Zigbee endpoint for zhawss."""


import asyncio
from typing import Any, Awaitable

import zigpy
from zigpy.typing import EndpointType as ZigpyEndpointType

from zhawss.platforms import discovery
from zhawss.platforms.registries import Platform
from zhawss.zigbee import registries
from zhawss.zigbee.cluster import ClusterHandler
from zhawss.zigbee.cluster.general import MultistateInput
from zhawss.zigbee.cluster.types import (
    ClientClusterHandlerType,
    ClusterHandlerDictType,
    ClusterHandlerType,
)
from zhawss.zigbee.decorators import CALLABLE_T
from zhawss.zigbee.types import DeviceType, EndpointType

ATTR_DEVICE_TYPE = "device_type"
ATTR_PROFILE_ID = "profile_id"
ATTR_IN_CLUSTERS = "in_clusters"
ATTR_OUT_CLUSTERS = "out_clusters"


class Endpoint:
    """Endpoint for zhawss."""

    def __init__(self, zigpy_endpoint: ZigpyEndpointType, device: DeviceType) -> None:
        """Initialize instance."""
        self._zigpy_endpoint: ZigpyEndpointType = zigpy_endpoint
        self._device: DeviceType = device
        self._all_cluster_handlers: ClusterHandlerDictType = {}
        self._claimed_cluster_handlers: ClusterHandlerDictType = {}
        self._client_cluster_handlers: dict[str, ClientClusterHandlerType] = {}
        self._unique_id: str = f"{str(device.ieee)}-{zigpy_endpoint.endpoint_id}"

    @property
    def device(self) -> DeviceType:
        """Return the device this endpoint belongs to."""
        return self._device

    @property
    def all_cluster_handlers(self) -> ClusterHandlerDictType:
        """All server cluster handlers of an endpoint."""
        return self._all_cluster_handlers

    @property
    def claimed_cluster_handlers(self) -> ClusterHandlerDictType:
        """Cluster handlers in use."""
        return self._claimed_cluster_handlers

    @property
    def client_cluster_handlers(self) -> dict[str, ClientClusterHandlerType]:
        """Return a dict of client cluster handlers."""
        return self._client_cluster_handlers

    @property
    def zigpy_endpoint(self) -> ZigpyEndpointType:
        """Return endpoint of zigpy device."""
        return self._zigpy_endpoint

    @property
    def id(self) -> int:
        """Return endpoint id."""
        return self._zigpy_endpoint.endpoint_id

    @property
    def unique_id(self):
        """Return the unique id for this endpoint."""
        return self._unique_id

    @property
    def zigbee_signature(self) -> tuple[int, dict[str, Any]]:
        """Get the zigbee signature for the endpoint this pool represents."""
        return (
            self.id,
            {
                ATTR_PROFILE_ID: self._zigpy_endpoint.profile_id,
                ATTR_DEVICE_TYPE: f"0x{self._zigpy_endpoint.device_type:04x}"
                if self._zigpy_endpoint.device_type is not None
                else "",
                ATTR_IN_CLUSTERS: [
                    f"0x{cluster_id:04x}"
                    for cluster_id in sorted(self._zigpy_endpoint.in_clusters)
                ],
                ATTR_OUT_CLUSTERS: [
                    f"0x{cluster_id:04x}"
                    for cluster_id in sorted(self._zigpy_endpoint.out_clusters)
                ],
            },
        )

    @classmethod
    def new(cls, zigpy_endpoint: ZigpyEndpointType, device: DeviceType) -> EndpointType:
        """Create new endpoint and populate cluster handlers."""
        endpoint = cls(zigpy_endpoint, device)
        endpoint.add_all_cluster_handlers()
        endpoint.add_client_cluster_handlers()
        discovery.PROBE.discover_entities(endpoint)
        return endpoint

    def add_all_cluster_handlers(self) -> None:
        """Create and add cluster handlers for all input clusters."""
        for cluster_id, cluster in self.zigpy_endpoint.in_clusters.items():
            cluster_handler_class = registries.CLUSTER_HANDLER_REGISTRY.get(
                cluster_id, ClusterHandler
            )
            # really ugly hack to deal with xiaomi using the door lock cluster
            # incorrectly.
            if (
                hasattr(cluster, "ep_attribute")
                and cluster_id == zigpy.zcl.clusters.closures.DoorLock.cluster_id
                and cluster.ep_attribute == "multistate_input"
            ):
                cluster_handler_class = MultistateInput
            # end of ugly hack
            cluster_handler = cluster_handler_class(cluster, self)
            """ TODO
            if cluster_handler.name == CLUSTER_HANDLER_POWER_CONFIGURATION:
                if (
                    self._channels.power_configuration_ch
                    or self._channels.zha_device.is_mains_powered
                ):
                    # on power configuration channel per device
                    continue
                self._channels.power_configuration_ch = cluster_handler
            elif cluster_handler.name == CLUSTER_HANDLER_IDENTIFY:
                self._channels.identify_ch = channel
            """
            self._all_cluster_handlers[cluster_handler.id] = cluster_handler

    def add_client_cluster_handlers(self) -> None:
        """Create client cluster handlers for all output clusters if in the registry."""
        for (
            cluster_id,
            cluster_handler_class,
        ) in registries.CLIENT_CLUSTER_HANDLER_REGISTRY.items():
            cluster = self.zigpy_endpoint.out_clusters.get(cluster_id)
            if cluster is not None:
                cluster_handler = cluster_handler_class(cluster, self)
                self.client_cluster_handlers[cluster_handler.id] = cluster_handler

    async def async_initialize(self, from_cache: bool = False) -> Awaitable[None]:
        """Initialize claimed cluster handlers."""
        await self._execute_handler_tasks("async_initialize", from_cache)

    async def async_configure(self) -> Awaitable[None]:
        """Configure claimed cluster handlers."""
        await self._execute_handler_tasks("async_configure")

    async def _execute_handler_tasks(
        self, func_name: str, *args: Any
    ) -> Awaitable[None]:
        """Add a throttled cluster handler task and swallow exceptions."""

        async def _throttle(coro):
            async with self._device.semaphore:
                return await coro

        cluster_handlers = [
            *self.claimed_cluster_handlers.values(),
            *self.client_cluster_handlers.values(),
        ]
        tasks = [_throttle(getattr(ch, func_name)(*args)) for ch in cluster_handlers]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for cluster_handler, outcome in zip(cluster_handlers, results):
            if isinstance(outcome, Exception):
                cluster_handler.warning(
                    "'%s' stage failed: %s", func_name, str(outcome)
                )
                continue
            cluster_handler.debug("'%s' stage succeeded", func_name)

    def async_new_entity(
        self,
        platform: Platform,
        entity_class: CALLABLE_T,
        unique_id: str,
        cluster_handlers: list[ClusterHandlerType],
    ):
        from zhawss.zigbee.device import DeviceStatus

        if self.device.status == DeviceStatus.INITIALIZED:
            return

        self.device.controller.server.data[platform].append(
            (entity_class, (unique_id, cluster_handlers, self, self.device))
        )

    def send_event(self, signal: dict[str, Any]) -> None:
        """Broadcast an event from this endpoint."""
        signal["endpoint_id"] = self.id
        self.device.send_event(signal)

    def claim_cluster_handlers(
        self, cluster_handlers: list[ClusterHandlerType]
    ) -> None:
        """Claim cluster handlers."""
        self.claimed_cluster_handlers.update({ch.id: ch for ch in cluster_handlers})

    def unclaimed_cluster_handlers(self) -> list[ClusterHandlerType]:
        """Return a list of available (unclaimed) cluster handlers."""
        claimed = set(self.claimed_cluster_handlers)
        available = set(self.all_cluster_handlers)
        return [
            self.all_cluster_handlers[cluster_id]
            for cluster_id in (available - claimed)
        ]

    """ TODO
    def zha_send_event(self, event_data: dict[str, str | int]) -> None:
        #Relay events to hass.
        self._channels.zha_send_event(
            {
                const.ATTR_UNIQUE_ID: self.unique_id,
                const.ATTR_ENDPOINT_ID: self.id,
                **event_data,
            }
        )
    """
