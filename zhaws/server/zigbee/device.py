"""Device for zhawss."""
from __future__ import annotations

import asyncio
from enum import Enum
import logging
import time
from typing import TYPE_CHECKING, Any, Callable, Final, Iterable, Union

from zigpy import types
from zigpy.device import Device as ZigpyDevice
import zigpy.exceptions
from zigpy.profiles import PROFILES
import zigpy.quirks
from zigpy.types.named import EUI64
from zigpy.zcl import Cluster
from zigpy.zcl.clusters.general import Groups
import zigpy.zdo.types as zdo_types

from zhaws.backports.enum import StrEnum
from zhaws.server.const import (
    DEVICE,
    EVENT,
    EVENT_TYPE,
    IEEE,
    MESSAGE_TYPE,
    NWK,
    EventTypes,
    MessageTypes,
)
from zhaws.server.decorators import periodic
from zhaws.server.platforms import PlatformEntity
from zhaws.server.util import LogMixin
from zhaws.server.zigbee.cluster import ZDOClusterHandler
from zhaws.server.zigbee.endpoint import Endpoint

_LOGGER = logging.getLogger(__name__)
_UPDATE_ALIVE_INTERVAL = (60, 90)
_CHECKIN_GRACE_PERIODS = 2

ATTR_ARGS: Final[str] = "args"
ATTR_ATTRIBUTE: Final[str] = "attribute"
ATTR_ATTRIBUTE_ID: Final[str] = "attribute_id"
ATTR_ATTRIBUTE_NAME: Final[str] = "attribute_name"
ATTR_AVAILABLE: Final[str] = "available"
ATTR_CLUSTER_ID: Final[str] = "cluster_id"
ATTR_CLUSTER_TYPE: Final[str] = "cluster_type"
ATTR_COMMAND: Final[str] = "command"
ATTR_COMMAND_TYPE: Final[str] = "command_type"
ATTR_DEVICE_IEEE: Final[str] = "device_ieee"
ATTR_DEVICE_TYPE: Final[str] = "device_type"
ATTR_ENDPOINTS: Final[str] = "endpoints"
ATTR_ENDPOINT_NAMES: Final[str] = "endpoint_names"
ATTR_ENDPOINT_ID: Final[str] = "endpoint_id"
ATTR_IN_CLUSTERS: Final[str] = "input_clusters"
ATTR_LAST_SEEN: Final[str] = "last_seen"
ATTR_LEVEL: Final[str] = "level"
ATTR_LQI: Final[str] = "lqi"
ATTR_MANUFACTURER: Final[str] = "manufacturer"
ATTR_MANUFACTURER_CODE: Final[str] = "manufacturer_code"
ATTR_MEMBERS: Final[str] = "members"
ATTR_MODEL: Final[str] = "model"
ATTR_NAME: Final[str] = "name"
ATTR_NEIGHBORS: Final[str] = "neighbors"
ATTR_NODE_DESCRIPTOR: Final[str] = "node_descriptor"
ATTR_OUT_CLUSTERS: Final[str] = "output_clusters"
ATTR_POWER_SOURCE: Final[str] = "power_source"
ATTR_PROFILE_ID: Final[str] = "profile_id"
ATTR_QUIRK_APPLIED: Final[str] = "quirk_applied"
ATTR_QUIRK_CLASS: Final[str] = "quirk_class"
ATTR_RSSI: Final[str] = "rssi"
ATTR_SIGNATURE: Final[str] = "signature"
ATTR_TYPE: Final[str] = "type"
ATTR_VALUE: Final[str] = "value"
ATTR_WARNING_DEVICE_DURATION: Final[str] = "duration"
ATTR_WARNING_DEVICE_MODE: Final[str] = "mode"
ATTR_WARNING_DEVICE_STROBE: Final[str] = "strobe"
ATTR_WARNING_DEVICE_STROBE_DUTY_CYCLE: Final[str] = "duty_cycle"
ATTR_WARNING_DEVICE_STROBE_INTENSITY: Final[str] = "intensity"
POWER_MAINS_POWERED: Final[str] = "Mains"
POWER_BATTERY_OR_UNKNOWN: Final[str] = "Battery or Unknown"
UNKNOWN: Final[str] = "unknown"
UNKNOWN_MANUFACTURER: Final[str] = "unk_manufacturer"
UNKNOWN_MODEL: Final[str] = "unk_model"

CLUSTER_COMMAND_SERVER: Final[str] = "server"
CLUSTER_COMMANDS_CLIENT: Final[str] = "client_commands"
CLUSTER_COMMANDS_SERVER: Final[str] = "server_commands"
CLUSTER_TYPE_IN: Final[str] = "in"
CLUSTER_TYPE_OUT: Final[str] = "out"

CONF_DEFAULT_CONSIDER_UNAVAILABLE_MAINS: Final[int] = 60 * 60 * 2  # 2 hours
CONF_DEFAULT_CONSIDER_UNAVAILABLE_BATTERY: Final[int] = 60 * 60 * 6  # 6 hours

if TYPE_CHECKING:
    from typing_extensions import TypeAlias

    from zhaws.server.zigbee.controller import Controller

    CLUSTER_TYPE = Union[TypeAlias[CLUSTER_TYPE_IN], TypeAlias[CLUSTER_TYPE_OUT]]


class DeviceStatus(Enum):
    """Status of a device."""

    CREATED = 1
    INITIALIZED = 2


class DeviceEvents(StrEnum):
    """Events that devices can broadcast."""

    DEVICE_OFFLINE = "device_offline"
    DEVICE_ONLINE = "device_online"


class Device(LogMixin):
    """ZHAWSS Zigbee device object."""

    def __init__(
        self,
        zigpy_device: ZigpyDevice,
        controller: Controller,
        #       zha_gateway: zha_typing.ZhaGatewayType,
    ) -> None:
        """Initialize the gateway."""
        self._controller: Controller = controller
        self._zigpy_device: ZigpyDevice = zigpy_device
        #       self._zha_gateway = zha_gateway
        self._available: bool = False
        #       self._available_signal = f"{self.name}_{self.ieee}_{SIGNAL_AVAILABLE}"
        self._checkins_missed_count: int = 0
        self.unsubs: list[Callable[[], Any]] = []
        self.quirk_applied: bool = isinstance(
            self._zigpy_device, zigpy.quirks.CustomDevice
        )
        self.quirk_class: str = (
            f"{self._zigpy_device.__class__.__module__}."
            f"{self._zigpy_device.__class__.__name__}"
        )

        if self.is_mains_powered:
            self.consider_unavailable_time = CONF_DEFAULT_CONSIDER_UNAVAILABLE_MAINS
            """TODO
            self.consider_unavailable_time = async_get_zha_config_value(
                self._zha_gateway.config_entry,
                ZHA_OPTIONS,
                CONF_CONSIDER_UNAVAILABLE_MAINS,
                CONF_DEFAULT_CONSIDER_UNAVAILABLE_MAINS,
            )
            """
        else:
            self.consider_unavailable_time = CONF_DEFAULT_CONSIDER_UNAVAILABLE_BATTERY
            """TODO
            self.consider_unavailable_time = async_get_zha_config_value(
                self._zha_gateway.config_entry,
                ZHA_OPTIONS,
                CONF_CONSIDER_UNAVAILABLE_BATTERY,
                CONF_DEFAULT_CONSIDER_UNAVAILABLE_BATTERY,
            )
            """

        self._platform_entities: dict[str, PlatformEntity] = {}
        self.semaphore: asyncio.Semaphore = asyncio.Semaphore(3)
        self._zdo_handler: ZDOClusterHandler = ZDOClusterHandler(self)
        self.status: DeviceStatus = DeviceStatus.CREATED

        self._endpoints: dict[int, Endpoint] = {}
        for ep_id, endpoint in zigpy_device.endpoints.items():
            if ep_id != 0:
                self._endpoints[ep_id] = Endpoint.new(endpoint, self)

        self._check_alive_task = asyncio.create_task(self._check_available())

    @property
    def device(self) -> ZigpyDevice:
        """Return underlying Zigpy device."""
        return self._zigpy_device

    @property
    def name(self) -> str:
        """Return device name."""
        return f"{self.manufacturer} {self.model}"

    @property
    def ieee(self) -> EUI64:
        """Return ieee address for device."""
        return self._zigpy_device.ieee

    @property
    def manufacturer(self) -> str:
        """Return manufacturer for device."""
        if self._zigpy_device.manufacturer is None:
            return UNKNOWN_MANUFACTURER
        return self._zigpy_device.manufacturer

    @property
    def model(self) -> str:
        """Return model for device."""
        if self._zigpy_device.model is None:
            return UNKNOWN_MODEL
        return self._zigpy_device.model

    @property
    def manufacturer_code(self) -> int | None:
        """Return the manufacturer code for the device."""
        if self._zigpy_device.node_desc is None:
            return None

        return self._zigpy_device.node_desc.manufacturer_code

    @property
    def nwk(self) -> int:
        """Return nwk for device."""
        return self._zigpy_device.nwk

    @property
    def lqi(self) -> int:
        """Return lqi for device."""
        return self._zigpy_device.lqi

    @property
    def rssi(self) -> int:
        """Return rssi for device."""
        return self._zigpy_device.rssi

    @property
    def last_seen(self) -> float | None:
        """Return last_seen for device."""
        return self._zigpy_device.last_seen

    @property
    def is_mains_powered(self) -> bool | None:
        """Return true if device is mains powered."""
        if self._zigpy_device.node_desc is None:
            return None

        return self._zigpy_device.node_desc.is_mains_powered

    @property
    def device_type(self) -> str:
        """Return the logical device type for the device."""
        if self._zigpy_device.node_desc is None:
            return UNKNOWN

        return self._zigpy_device.node_desc.logical_type.name

    @property
    def power_source(self) -> str:
        """Return the power source for the device."""
        return (
            POWER_MAINS_POWERED if self.is_mains_powered else POWER_BATTERY_OR_UNKNOWN
        )

    @property
    def is_router(self) -> bool | None:
        """Return true if this is a routing capable device."""
        if self._zigpy_device.node_desc is None:
            return None

        return self._zigpy_device.node_desc.is_router

    @property
    def is_coordinator(self) -> bool | None:
        """Return true if this device represents the coordinator."""
        if self._zigpy_device.node_desc is None:
            return None

        return self._zigpy_device.node_desc.is_coordinator

    @property
    def is_end_device(self) -> bool | None:
        """Return true if this device is an end device."""
        if self._zigpy_device.node_desc is None:
            return None

        return self._zigpy_device.node_desc.is_end_device

    @property
    def is_groupable(self) -> bool:
        """Return true if this device has a group cluster."""
        if self.is_coordinator:
            return True
        elif self.available:
            return bool(self.async_get_groupable_endpoints())

        return False

    @property
    def skip_configuration(self) -> bool:
        """Return true if the device should not issue configuration related commands."""
        return self._zigpy_device.skip_configuration

    @property
    def controller(self) -> Controller:
        # Return the controller for this device.
        return self._controller

    @property
    def device_automation_triggers(self) -> dict:
        """Return the device automation triggers for this device."""
        triggers = {
            ("device_offline", "device_offline"): {
                "device_event_type": "device_offline"
            }
        }

        if hasattr(self._zigpy_device, "device_automation_triggers"):
            triggers.update(self._zigpy_device.device_automation_triggers)

        return triggers

    @property
    def available(self) -> bool:
        """Return True if device is available."""
        return self._available

    @available.setter
    def available(self, new_availability: bool) -> None:
        """Set device availability."""
        self._available = new_availability

    @property
    def zigbee_signature(self) -> dict[str, Any]:
        # Get zigbee signature for this device.
        return {
            ATTR_NODE_DESCRIPTOR: self._zigpy_device.node_desc.as_dict(),
            ATTR_ENDPOINTS: {
                signature[0]: signature[1]
                for signature in [
                    endpoint.zigbee_signature for endpoint in self._endpoints.values()
                ]
            },
        }

    @property
    def platform_entities(self) -> dict[str, PlatformEntity]:
        """Return the platform entities for this device."""
        return self._platform_entities

    def get_platform_entity(self, unique_id: str) -> PlatformEntity:
        """Get a platform entity by unique id"""
        entity = self._platform_entities.get(unique_id)
        if entity is None:
            raise ValueError(f"Entity {unique_id} not found")
        return entity

    """ TODO
    def async_update_sw_build_id(self, sw_version: int):
        #Update device sw version.
        if self.device_id is None:
            return
        self._zha_gateway.ha_device_registry.async_update_device(
            self.device_id, sw_version=f"0x{sw_version:08x}"
        )
    """

    def send_event(self, signal: dict[str, Any]) -> None:
        """Broadcast an event from this device."""
        signal[DEVICE] = {IEEE: str(self.ieee)}
        self.controller.server.client_manager.broadcast(signal)

    @periodic(_UPDATE_ALIVE_INTERVAL)
    async def _check_available(self) -> None:
        # don't flip the availability state of the coordinator
        if self.is_coordinator:
            return
        if self.last_seen is None:
            self.update_available(False)
            return

        difference = time.time() - self.last_seen
        if difference < self.consider_unavailable_time:
            self.update_available(True)
            self._checkins_missed_count = 0
            return

        if (
            self._checkins_missed_count >= _CHECKIN_GRACE_PERIODS
            or self.manufacturer == "LUMI"
            or not self._endpoints
        ):
            self.update_available(False)
            return

        self._checkins_missed_count += 1
        self.debug(
            "Attempting to checkin with device - missed checkins: %s",
            self._checkins_missed_count,
        )
        for id, endpoint in self._endpoints.items():
            if f"{id}:0x0000" in endpoint.all_cluster_handlers:
                basic_ch = endpoint.all_cluster_handlers[f"{id}:0x0000"]
                break
        if not basic_ch:
            self.debug("does not have a mandatory basic cluster")
            self.update_available(False)
            return
        res = await basic_ch.get_attribute_value(ATTR_MANUFACTURER, from_cache=False)
        if res is not None:
            self._checkins_missed_count = 0

    def update_available(self, available: bool) -> None:
        """Update device availability and signal entities."""
        availability_changed = self.available ^ available
        self.available = available
        if availability_changed and available:
            # reinit channels then signal entities
            asyncio.create_task(self._async_became_available())
            return

        if availability_changed and not available:
            message: dict[str, Any] = {
                MESSAGE_TYPE: MessageTypes.EVENT,
                EVENT_TYPE: EventTypes.DEVICE_EVENT,
                EVENT: DeviceEvents.DEVICE_OFFLINE,
            }
            self.send_event(message)

    async def _async_became_available(self) -> None:
        """Update device availability and signal entities."""
        await self.async_initialize(False)
        message: dict[str, Any] = {
            MESSAGE_TYPE: MessageTypes.EVENT,
            EVENT_TYPE: EventTypes.DEVICE_EVENT,
            EVENT: DeviceEvents.DEVICE_ONLINE,
        }
        self.send_event(message)

    @property
    def device_info(self) -> dict[str, Any]:
        """Return a device description for device."""
        ieee = str(self.ieee)
        time_struct = time.localtime(self.last_seen)
        update_time = time.strftime("%Y-%m-%dT%H:%M:%S", time_struct)
        return {
            IEEE: ieee,
            NWK: f"0x{self.nwk:04x}",
            ATTR_MANUFACTURER: self.manufacturer,
            ATTR_MODEL: self.model,
            ATTR_NAME: self.name or ieee,
            ATTR_QUIRK_APPLIED: self.quirk_applied,
            ATTR_QUIRK_CLASS: self.quirk_class,
            ATTR_MANUFACTURER_CODE: self.manufacturer_code,
            ATTR_POWER_SOURCE: self.power_source,
            ATTR_LQI: self.lqi,
            ATTR_RSSI: self.rssi,
            ATTR_LAST_SEEN: update_time,
            ATTR_AVAILABLE: self.available,
            ATTR_DEVICE_TYPE: self.device_type,
            ATTR_SIGNATURE: self.zigbee_signature,
        }

    async def async_configure(self) -> None:
        """Configure the device."""
        """ TODO
        should_identify = async_get_zha_config_value(
            self._zha_gateway.config_entry,
            ZHA_OPTIONS,
            CONF_ENABLE_IDENTIFY_ON_JOIN,
            True,
        )
        """
        self.debug("started configuration")
        await self._zdo_handler.async_configure()
        self._zdo_handler.debug("'async_configure' stage succeeded")
        await asyncio.gather(
            *(endpoint.async_configure() for endpoint in self._endpoints.values())
        )
        """ TODO
        async_dispatcher_send(
            self.zha_device.hass,
            const.ZHA_CHANNEL_MSG,
            {
                const.ATTR_TYPE: const.ZHA_CHANNEL_CFG_DONE,
            },
        )
        """
        self.debug("completed configuration")
        """TODO
        entry = self.gateway.zha_storage.async_create_or_update_device(self)
        self.debug("stored in registry: %s", entry)
        """

        """ TODO
        if (
            should_identify
            and self._channels.identify_ch is not None
            and not self.skip_configuration
        ):
            await self._channels.identify_ch.trigger_effect(
                EFFECT_OKAY, EFFECT_DEFAULT_VARIANT
            )
        """

    async def async_initialize(self, from_cache: bool = False) -> None:
        """Initialize cluster handlers."""
        self.debug("started initialization")
        await self._zdo_handler.async_initialize(from_cache)
        self._zdo_handler.debug("'async_initialize' stage succeeded")
        await asyncio.gather(
            *(
                endpoint.async_initialize(from_cache)
                for endpoint in self._endpoints.values()
            )
        )
        self.debug("power source: %s", self.power_source)
        self.status = DeviceStatus.INITIALIZED
        self.debug("completed initialization")

    def async_cleanup_handles(self) -> None:
        """Unsubscribe the dispatchers and timers."""
        for unsubscribe in self.unsubs:
            unsubscribe()

    def async_update_last_seen(self, last_seen: float) -> None:
        """Set last seen on the zigpy device."""
        if self._zigpy_device.last_seen is None and last_seen is not None:
            self._zigpy_device.last_seen = last_seen

    @property
    def zha_device_info(self) -> dict:
        """Get ZHA device information."""
        device_info = {}
        device_info.update(self.device_info)
        device_info["entities"] = {
            unique_id: platform_entity.to_json()
            for unique_id, platform_entity in self.platform_entities.items()
        }

        # Return the neighbor information
        device_info[ATTR_NEIGHBORS] = [
            {
                "device_type": neighbor.neighbor.device_type.name,
                "rx_on_when_idle": neighbor.neighbor.rx_on_when_idle.name,
                "relationship": neighbor.neighbor.relationship.name,
                "extended_pan_id": str(neighbor.neighbor.extended_pan_id),
                IEEE: str(neighbor.neighbor.ieee),
                NWK: f"0x{neighbor.neighbor.nwk:04x}",
                "permit_joining": neighbor.neighbor.permit_joining.name,
                "depth": str(neighbor.neighbor.depth),
                "lqi": str(neighbor.neighbor.lqi),
            }
            for neighbor in self._zigpy_device.neighbors
        ]

        # Return endpoint device type Names
        names = []
        for endpoint in (ep for epid, ep in self.device.endpoints.items() if epid):
            profile = PROFILES.get(endpoint.profile_id)
            if profile and endpoint.device_type is not None:
                # DeviceType provides undefined enums
                names.append({ATTR_NAME: profile.DeviceType(endpoint.device_type).name})
            else:
                names.append(
                    {
                        ATTR_NAME: f"unknown {endpoint.device_type} device_type "
                        f"of 0x{(endpoint.profile_id or 0xFFFF):04x} profile id"
                    }
                )
        device_info[ATTR_ENDPOINT_NAMES] = names

        return device_info

    def async_get_clusters(self) -> dict[int, dict[CLUSTER_TYPE, list[int]]]:
        """Get all clusters for this device."""
        return {
            ep_id: {
                CLUSTER_TYPE_IN: endpoint.in_clusters,
                CLUSTER_TYPE_OUT: endpoint.out_clusters,
            }
            for (ep_id, endpoint) in self._zigpy_device.endpoints.items()
            if ep_id != 0
        }

    def async_get_groupable_endpoints(self) -> list[int]:
        """Get device endpoints that have a group 'in' cluster."""
        return [
            ep_id
            for (ep_id, clusters) in self.async_get_clusters().items()
            if Groups.cluster_id in clusters[CLUSTER_TYPE_IN]
        ]

    def async_get_std_clusters(self) -> dict[str, dict[CLUSTER_TYPE, int]]:
        """Get ZHA and ZLL clusters for this device."""

        return {
            ep_id: {
                CLUSTER_TYPE_IN: endpoint.in_clusters,
                CLUSTER_TYPE_OUT: endpoint.out_clusters,
            }
            for (ep_id, endpoint) in self._zigpy_device.endpoints.items()
            if ep_id != 0 and endpoint.profile_id in PROFILES
        }

    def async_get_cluster(
        self,
        endpoint_id: int,
        cluster_id: int,
        cluster_type: CLUSTER_TYPE = CLUSTER_TYPE_IN,
    ) -> Cluster:
        """Get zigbee cluster from this entity."""
        clusters = self.async_get_clusters()
        return clusters[endpoint_id][cluster_type][cluster_id]

    def async_get_cluster_attributes(
        self,
        endpoint_id: int,
        cluster_id: int,
        cluster_type: CLUSTER_TYPE = CLUSTER_TYPE_IN,
    ) -> dict | None:
        """Get zigbee attributes for specified cluster."""
        cluster = self.async_get_cluster(endpoint_id, cluster_id, cluster_type)
        if cluster is None:
            return None
        return cluster.attributes

    def async_get_cluster_commands(
        self,
        endpoint_id: int,
        cluster_id: int,
        cluster_type: CLUSTER_TYPE = CLUSTER_TYPE_IN,
    ) -> dict | None:
        """Get zigbee commands for specified cluster."""
        cluster = self.async_get_cluster(endpoint_id, cluster_id, cluster_type)
        if cluster is None:
            return None
        return {
            CLUSTER_COMMANDS_CLIENT: cluster.client_commands,
            CLUSTER_COMMANDS_SERVER: cluster.server_commands,
        }

    async def write_zigbee_attribute(
        self,
        endpoint_id: int,
        cluster_id: int,
        attribute: str | int,
        value: Any,
        cluster_type: CLUSTER_TYPE = CLUSTER_TYPE_IN,
        manufacturer: int | None = None,
    ) -> list | None:
        """Write a value to a zigbee attribute for a cluster in this entity."""
        cluster = self.async_get_cluster(endpoint_id, cluster_id, cluster_type)
        if cluster is None:
            return None

        try:
            response = await cluster.write_attributes(
                {attribute: value}, manufacturer=manufacturer
            )
            self.debug(
                "set: %s for attr: %s to cluster: %s for ept: %s - res: %s",
                value,
                attribute,
                cluster_id,
                endpoint_id,
                response,
            )
            return response
        except zigpy.exceptions.ZigbeeException as exc:
            self.debug(
                "failed to set attribute: %s %s %s %s %s",
                f"{ATTR_VALUE}: {value}",
                f"{ATTR_ATTRIBUTE}: {attribute}",
                f"{ATTR_CLUSTER_ID}: {cluster_id}",
                f"{ATTR_ENDPOINT_ID}: {endpoint_id}",
                exc,
            )
            return None

    async def issue_cluster_command(
        self,
        endpoint_id: int,
        cluster_id: int,
        command: int,
        command_type: str,
        *args: Any,
        cluster_type: CLUSTER_TYPE = CLUSTER_TYPE_IN,
        manufacturer: int | None = None,
    ) -> Any | None:
        """Issue a command against specified zigbee cluster on this entity."""
        cluster = self.async_get_cluster(endpoint_id, cluster_id, cluster_type)
        if cluster is None:
            return None
        if command_type == CLUSTER_COMMAND_SERVER:
            response = await cluster.command(
                command, *args, manufacturer=manufacturer, expect_reply=True
            )
        else:
            response = await cluster.client_command(command, *args)

        self.debug(
            "Issued cluster command: %s %s %s %s %s %s %s",
            f"{ATTR_CLUSTER_ID}: {cluster_id}",
            f"{ATTR_COMMAND}: {command}",
            f"{ATTR_COMMAND_TYPE}: {command_type}",
            f"{ATTR_ARGS}: {args}",
            f"{ATTR_CLUSTER_ID}: {cluster_type}",
            f"{ATTR_MANUFACTURER}: {manufacturer}",
            f"{ATTR_ENDPOINT_ID}: {endpoint_id}",
        )
        return response

    async def async_add_to_group(self, group_id: int) -> None:
        """Add this device to the provided zigbee group."""
        try:
            await self._zigpy_device.add_to_group(group_id)
        except (zigpy.exceptions.ZigbeeException, asyncio.TimeoutError) as ex:
            self.debug(
                "Failed to add device '%s' to group: 0x%04x ex: %s",
                self._zigpy_device.ieee,
                group_id,
                str(ex),
            )

    async def async_remove_from_group(self, group_id: int) -> None:
        """Remove this device from the provided zigbee group."""
        try:
            await self._zigpy_device.remove_from_group(group_id)
        except (zigpy.exceptions.ZigbeeException, asyncio.TimeoutError) as ex:
            self.debug(
                "Failed to remove device '%s' from group: 0x%04x ex: %s",
                self._zigpy_device.ieee,
                group_id,
                str(ex),
            )

    async def async_add_endpoint_to_group(
        self, endpoint_id: int, group_id: int
    ) -> None:
        """Add the device endpoint to the provided zigbee group."""
        try:
            await self._zigpy_device.endpoints[int(endpoint_id)].add_to_group(group_id)
        except (zigpy.exceptions.ZigbeeException, asyncio.TimeoutError) as ex:
            self.debug(
                "Failed to add endpoint: %s for device: '%s' to group: 0x%04x ex: %s",
                endpoint_id,
                self._zigpy_device.ieee,
                group_id,
                str(ex),
            )

    async def async_remove_endpoint_from_group(
        self, endpoint_id: int, group_id: int
    ) -> None:
        """Remove the device endpoint from the provided zigbee group."""
        try:
            await self._zigpy_device.endpoints[int(endpoint_id)].remove_from_group(
                group_id
            )
        except (zigpy.exceptions.ZigbeeException, asyncio.TimeoutError) as ex:
            self.debug(
                "Failed to remove endpoint: %s for device '%s' from group: 0x%04x ex: %s",
                endpoint_id,
                self._zigpy_device.ieee,
                group_id,
                str(ex),
            )

    async def async_bind_to_group(
        self, group_id: int, cluster_bindings: Iterable
    ) -> None:
        """Directly bind this device to a group for the given clusters."""
        await self._async_group_binding_operation(
            group_id, zdo_types.ZDOCmd.Bind_req, cluster_bindings
        )

    async def async_unbind_from_group(
        self, group_id: int, cluster_bindings: Iterable
    ) -> None:
        """Unbind this device from a group for the given clusters."""
        await self._async_group_binding_operation(
            group_id, zdo_types.ZDOCmd.Unbind_req, cluster_bindings
        )

    async def _async_group_binding_operation(
        self,
        group_id: int,
        operation: zdo_types.ZDOCmd.Bind_req | zdo_types.ZDOCmd.Unbind_req,
        cluster_bindings: Iterable,
    ) -> None:
        """Create or remove a direct zigbee binding between a device and a group."""

        zdo = self._zigpy_device.zdo
        op_msg = "0x%04x: %s %s, ep: %s, cluster: %s to group: 0x%04x"
        destination_address = zdo_types.MultiAddress()
        destination_address.addrmode = types.uint8_t(1)
        destination_address.nwk = types.uint16_t(group_id)

        tasks = []

        for cluster_binding in cluster_bindings:
            if cluster_binding.endpoint_id == 0:
                continue
            if (
                cluster_binding.id
                in self._zigpy_device.endpoints[
                    cluster_binding.endpoint_id
                ].out_clusters
            ):
                op_params = (
                    self.nwk,
                    operation.name,
                    str(self.ieee),
                    cluster_binding.endpoint_id,
                    cluster_binding.id,
                    group_id,
                )
                zdo.debug(f"processing {op_msg}", *op_params)
                tasks.append(
                    (
                        zdo.request(
                            operation,
                            self.ieee,
                            cluster_binding.endpoint_id,
                            cluster_binding.id,
                            destination_address,
                        ),
                        op_msg,
                        op_params,
                    )
                )
        res = await asyncio.gather(*(t[0] for t in tasks), return_exceptions=True)
        for outcome, log_msg in zip(res, tasks):
            if isinstance(outcome, Exception):
                fmt = f"{log_msg[1]} failed: %s"
            else:
                fmt = f"{log_msg[1]} completed: %s"
            zdo.debug(fmt, *(log_msg[2] + (outcome,)))

    def log(self, level: int, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log a message."""
        msg = f"[%s](%s): {msg}"
        args = (self.nwk, self.model) + args
        _LOGGER.log(level, msg, *args, **kwargs)
