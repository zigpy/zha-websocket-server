"""Base classes for zigbee cluster handlers."""
from __future__ import annotations

import asyncio
from enum import Enum
from functools import partialmethod
import logging
from typing import Any, Awaitable, Dict

import zigpy.exceptions
from zigpy.zcl import Cluster as ZigpyCluster
from zigpy.zcl.foundation import Status

from zhawss.util import LogMixin
from zhawss.zigbee.cluster.const import (
    CLUSTER_HANDLER_ZDO,
    CLUSTER_READS_PER_REQ,
    REPORT_CONFIG_ATTR_PER_REQ,
)
from zhawss.zigbee.cluster.decorators import decorate_command, retryable_request
from zhawss.zigbee.cluster.util import safe_read
from zhawss.zigbee.types import DeviceType, EndpointType

_LOGGER = logging.getLogger(__name__)


class ClusterHandlerStatus(Enum):
    """Status of a cluster handler."""

    CREATED = 1
    CONFIGURED = 2
    INITIALIZED = 3


class ClusterHandler(LogMixin):
    """Base cluster handler for a Zigbee cluster handler."""

    REPORT_CONFIG: tuple[dict[int | str, tuple[int, int, int | float]]] = ()
    BIND: bool = True

    # Dict of attributes to read on cluster handler initialization.
    # Dict keys -- attribute ID or names, with bool value indicating whether a cached
    # attribute read is acceptable.
    ZCL_INIT_ATTRS: dict[int | str, bool] = {}

    def __init__(self, cluster: ZigpyCluster, endpoint: EndpointType) -> None:
        """Initialize ClusterHandler."""
        self._generic_id: str = f"channel_0x{cluster.cluster_id:04x}"
        self._endpoint: EndpointType = endpoint
        self._cluster: ZigpyCluster = cluster
        self._id: str = f"{endpoint.id}:0x{cluster.cluster_id:04x}"
        unique_id: str = endpoint.unique_id.replace("-", ":")
        self._unique_id = f"{unique_id}:0x{cluster.cluster_id:04x}"
        if not hasattr(self, "_value_attribute") and self.REPORT_CONFIG:
            attr = self.REPORT_CONFIG[0].get("attr")
            if isinstance(attr, str):
                self.value_attribute = self.cluster.attridx.get(attr)
            else:
                self.value_attribute = attr
        self._status: ClusterHandlerStatus = ClusterHandlerStatus.CREATED
        self._cluster.add_listener(self)
        self.data_cache: Dict[str, Any] = {}

    @property
    def id(self) -> str:
        """Return cluster handler id."""
        return self._id

    @property
    def generic_id(self) -> str:
        """Return the generic id for this cluster handler."""
        return self._generic_id

    @property
    def unique_id(self) -> str:
        """Return the unique id for this cluster handler."""
        return self._unique_id

    @property
    def cluster(self) -> ZigpyCluster:
        """Return the zigpy cluster for this cluster handler."""
        return self._cluster

    @property
    def name(self) -> str:
        """Return friendly name."""
        return self.cluster.ep_attribute or self._generic_id

    @property
    def status(self) -> ClusterHandlerStatus:
        """Return the status of the cluster handler."""
        return self._status

    def __hash__(self) -> int:
        """Make this a hashable."""
        return hash(self._unique_id)

    def async_send_signal(self, signal: str, *args: Any) -> None:
        """Send a signal through hass dispatcher."""
        self._ch_pool.async_send_signal(signal, *args)

    async def bind(self) -> Awaitable[None]:
        """Bind a zigbee cluster.

        This also swallows ZigbeeException exceptions that are thrown when
        devices are unreachable.
        """
        try:
            res = await self.cluster.bind()
            self.debug("bound '%s' cluster: %s", self.cluster.ep_attribute, res[0])
            """ TODO
            async_dispatcher_send(
                self._ch_pool.hass,
                ZHA_CHANNEL_MSG,
                {
                    ATTR_TYPE: ZHA_CHANNEL_MSG_BIND,
                    ZHA_CHANNEL_MSG_DATA: {
                        "cluster_name": self.cluster.name,
                        "cluster_id": self.cluster.cluster_id,
                        "success": res[0] == 0,
                    },
                },
            )
            """
        except (zigpy.exceptions.ZigbeeException, asyncio.TimeoutError) as ex:
            self.debug(
                "Failed to bind '%s' cluster: %s", self.cluster.ep_attribute, str(ex)
            )
            """ TODO
            async_dispatcher_send(
                self._ch_pool.hass,
                ZHA_CHANNEL_MSG,
                {
                    ATTR_TYPE: ZHA_CHANNEL_MSG_BIND,
                    ZHA_CHANNEL_MSG_DATA: {
                        "cluster_name": self.cluster.name,
                        "cluster_id": self.cluster.cluster_id,
                        "success": False,
                    },
                },
            )
            """

    async def configure_reporting(self) -> Awaitable[None]:
        """Configure attribute reporting for a cluster.

        This also swallows ZigbeeException exceptions that are thrown when
        devices are unreachable.
        """
        event_data = {}
        kwargs = {}
        if self.cluster.cluster_id >= 0xFC00 and self._ch_pool.manufacturer_code:
            kwargs["manufacturer"] = self._ch_pool.manufacturer_code

        for attr_report in self.REPORT_CONFIG:
            attr, config = attr_report["attr"], attr_report["config"]
            attr_name = self.cluster.attributes.get(attr, [attr])[0]
            event_data[attr_name] = {
                "min": config[0],
                "max": config[1],
                "id": attr,
                "name": attr_name,
                "change": config[2],
                "success": False,
            }

        to_configure = [*self.REPORT_CONFIG]
        chunk, rest = (
            to_configure[:REPORT_CONFIG_ATTR_PER_REQ],
            to_configure[REPORT_CONFIG_ATTR_PER_REQ:],
        )
        while chunk:
            reports = {rec["attr"]: rec["config"] for rec in chunk}
            try:
                res = await self.cluster.configure_reporting_multiple(reports, **kwargs)
                self._configure_reporting_status(reports, res[0])
                # if we get a response, then it's a success
                for attr_stat in event_data.values():
                    attr_stat["success"] = True
            except (zigpy.exceptions.ZigbeeException, asyncio.TimeoutError) as ex:
                self.debug(
                    "failed to set reporting on '%s' cluster for: %s",
                    self.cluster.ep_attribute,
                    str(ex),
                )
                break
            chunk, rest = (
                rest[:REPORT_CONFIG_ATTR_PER_REQ],
                rest[REPORT_CONFIG_ATTR_PER_REQ:],
            )

        """ TODO
        async_dispatcher_send(
            self._ch_pool.hass,
            ZHA_CHANNEL_MSG,
            {
                ATTR_TYPE: ZHA_CHANNEL_MSG_CFG_RPT,
                ZHA_CHANNEL_MSG_DATA: {
                    "cluster_name": self.cluster.name,
                    "cluster_id": self.cluster.cluster_id,
                    "attributes": event_data,
                },
            },
        )
        """

    def _configure_reporting_status(
        self, attrs: dict[int | str, tuple], res: list | tuple
    ) -> None:
        """Parse configure reporting result."""
        if not isinstance(res, list):
            # assume default response
            self.debug(
                "attr reporting for '%s' on '%s': %s",
                attrs,
                self.name,
                res,
            )
            return
        if res[0].status == Status.SUCCESS and len(res) == 1:
            self.debug(
                "Successfully configured reporting for '%s' on '%s' cluster: %s",
                attrs,
                self.name,
                res,
            )
            return

        failed = [
            self.cluster.attributes.get(r.attrid, [r.attrid])[0]
            for r in res
            if r.status != Status.SUCCESS
        ]
        attrs = {self.cluster.attributes.get(r, [r])[0] for r in attrs}
        self.debug(
            "Successfully configured reporting for '%s' on '%s' cluster",
            attrs - set(failed),
            self.name,
        )
        self.debug(
            "Failed to configure reporting for '%s' on '%s' cluster: %s",
            failed,
            self.name,
            res,
        )

    async def async_configure(self) -> Awaitable[None]:
        """Set cluster binding and attribute reporting."""
        if not self._ch_pool.skip_configuration:
            if self.BIND:
                await self.bind()
            if self.cluster.is_server:
                await self.configure_reporting()
            ch_specific_cfg = getattr(self, "async_configure_handler_specific", None)
            if ch_specific_cfg:
                await ch_specific_cfg()
            self.debug("finished cluster handler configuration")
        else:
            self.debug("skipping cluster handler configuration")
        self._status = ClusterHandlerStatus.CONFIGURED

    @retryable_request(delays=(1, 1, 3))
    async def async_initialize(self, from_cache: bool) -> Awaitable[None]:
        """Initialize cluster handler."""
        if not from_cache and self._ch_pool.skip_configuration:
            self._status = ClusterHandlerStatus.INITIALIZED
            return

        self.debug("initializing cluster handler: from_cache: %s", from_cache)
        cached = [a for a, cached in self.ZCL_INIT_ATTRS.items() if cached]
        uncached = [a for a, cached in self.ZCL_INIT_ATTRS.items() if not cached]
        uncached.extend([cfg["attr"] for cfg in self.REPORT_CONFIG])

        if cached:
            await self._get_attributes(True, cached, from_cache=True)
        if uncached:
            await self._get_attributes(True, uncached, from_cache=from_cache)

        ch_specific_init = getattr(self, "async_initialize_handler_specific", None)
        if ch_specific_init:
            await ch_specific_init(from_cache=from_cache)

        self.debug("finished cluster handler initialization")
        self._status = ClusterHandlerStatus.INITIALIZED

    def cluster_command(self, tsn, command_id, args) -> None:
        """Handle commands received to this cluster."""

    def attribute_updated(self, attrid, value) -> None:
        """Handle attribute updates on this cluster."""
        """ TODO
        self.async_send_signal(
            f"{self.unique_id}_{SIGNAL_ATTR_UPDATED}",
            attrid,
            self.cluster.attributes.get(attrid, [attrid])[0],
            value,
        )
        """

    def zdo_command(self, *args, **kwargs) -> None:
        """Handle ZDO commands on this cluster."""

    def zha_send_event(self, command: str, args: int | dict) -> None:
        """Relay events to hass."""
        """ TODO
        self._ch_pool.zha_send_event(
            {
                ATTR_UNIQUE_ID: self.unique_id,
                ATTR_CLUSTER_ID: self.cluster.cluster_id,
                ATTR_COMMAND: command,
                ATTR_ARGS: args,
            }
        )
        """

    async def async_update(self) -> Awaitable[None]:
        """Retrieve latest state from cluster."""

    async def get_attribute_value(self, attribute, from_cache=True) -> Awaitable[Any]:
        """Get the value for an attribute."""
        manufacturer = None
        manufacturer_code = self._ch_pool.manufacturer_code
        if self.cluster.cluster_id >= 0xFC00 and manufacturer_code:
            manufacturer = manufacturer_code
        result = await safe_read(
            self._cluster,
            [attribute],
            allow_cache=from_cache,
            only_cache=from_cache and not self._ch_pool.is_mains_powered,
            manufacturer=manufacturer,
        )
        return result.get(attribute)

    async def _get_attributes(
        self,
        raise_exceptions: bool,
        attributes: list[int | str],
        from_cache: bool = True,
    ) -> dict[int | str, Any]:
        """Get the values for a list of attributes."""
        manufacturer = None
        manufacturer_code = self._ch_pool.manufacturer_code
        if self.cluster.cluster_id >= 0xFC00 and manufacturer_code:
            manufacturer = manufacturer_code
        chunk = attributes[:CLUSTER_READS_PER_REQ]
        rest = attributes[CLUSTER_READS_PER_REQ:]
        result = {}
        while chunk:
            try:
                read, _ = await self.cluster.read_attributes(
                    attributes,
                    allow_cache=from_cache,
                    only_cache=from_cache and not self._ch_pool.is_mains_powered,
                    manufacturer=manufacturer,
                )
                result.update(read)
            except (asyncio.TimeoutError, zigpy.exceptions.ZigbeeException) as ex:
                self.debug(
                    "failed to get attributes '%s' on '%s' cluster: %s",
                    attributes,
                    self.cluster.ep_attribute,
                    str(ex),
                )
                if raise_exceptions:
                    raise
            chunk = rest[:CLUSTER_READS_PER_REQ]
            rest = rest[CLUSTER_READS_PER_REQ:]
        return result

    get_attributes = partialmethod(_get_attributes, False)

    def log(self, level, msg, *args) -> None:
        """Log a message."""
        msg = f"[%s:%s]: {msg}"
        args = (self._ch_pool.nwk, self._id) + args
        _LOGGER.log(level, msg, *args)

    def __getattr__(self, name):
        """Get attribute or a decorated cluster command."""
        if hasattr(self._cluster, name) and callable(getattr(self._cluster, name)):
            command = getattr(self._cluster, name)
            command.__name__ = name
            return decorate_command(self, command)
        return self.__getattribute__(name)


class ZDOClusterHandler(LogMixin):
    """Cluster handler for ZDO events."""

    def __init__(self, device: DeviceType):
        """Initialize ZDOClusterHandler."""
        self.name: str = CLUSTER_HANDLER_ZDO
        self._cluster: ZigpyCluster = device.device.endpoints[0]
        self._device: DeviceType = device
        self._status: ClusterHandlerStatus = ClusterHandlerStatus.CREATED
        self._unique_id: str = f"{str(device.ieee)}:{device.name}_ZDO"
        self._cluster.add_listener(self)

    @property
    def unique_id(self) -> str:
        """Return the unique id for this cluster handler."""
        return self._unique_id

    @property
    def cluster(self) -> ZigpyCluster:
        """Return the aigpy cluster for this cluster handler."""
        return self._cluster

    @property
    def status(self) -> ClusterHandlerStatus:
        """Return the status of the cluster handler."""
        return self._status

    def device_announce(self, zigpy_device) -> None:
        """Device announce handler."""

    def permit_duration(self, duration) -> None:
        """Permit handler."""

    async def async_initialize(self, from_cache) -> Awaitable[None]:
        """Initialize cluster handler."""
        self._status = ClusterHandlerStatus.INITIALIZED

    async def async_configure(self) -> Awaitable[None]:
        """Configure cluster handler."""
        self._status = ClusterHandlerStatus.CONFIGURED

    def log(self, level, msg, *args) -> None:
        """Log a message."""
        msg = f"[%s:ZDO](%s): {msg}"
        args = (self._device.nwk, self._device.model) + args
        _LOGGER.log(level, msg, *args)


class ClientClusterHandler(ClusterHandler):
    """Cluster handler for Zigbee client (output) clusters."""

    def attribute_updated(self, attrid, value) -> None:
        """Handle an attribute updated on this cluster."""
        """ TODO
        self.zha_send_event(
            SIGNAL_ATTR_UPDATED,
            {
                ATTR_ATTRIBUTE_ID: attrid,
                ATTR_ATTRIBUTE_NAME: self._cluster.attributes.get(attrid, ["Unknown"])[
                    0
                ],
                ATTR_VALUE: value,
            },
        )
        """

    def cluster_command(self, tsn, command_id, args) -> None:
        """Handle a cluster command received on this cluster."""
        if (
            self._cluster.server_commands is not None
            and self._cluster.server_commands.get(command_id) is not None
        ):
            self.zha_send_event(self._cluster.server_commands.get(command_id)[0], args)