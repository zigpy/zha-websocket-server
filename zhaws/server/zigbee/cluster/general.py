"""General cluster handlers module for zhawss."""
from __future__ import annotations

import asyncio
from collections.abc import Coroutine
from typing import TYPE_CHECKING, Any, Literal

import zigpy.exceptions
from zigpy.zcl import Cluster as ZigpyClusterType
from zigpy.zcl.clusters import general
from zigpy.zcl.foundation import Status

from zhaws.model import BaseEvent
from zhaws.server.zigbee import registries
from zhaws.server.zigbee.cluster import (
    CLUSTER_HANDLER_EVENT,
    ClientClusterHandler,
    ClusterAttributeUpdatedEvent,
    ClusterHandler,
)
from zhaws.server.zigbee.cluster.const import (
    REPORT_CONFIG_ASAP,
    REPORT_CONFIG_BATTERY_SAVE,
    REPORT_CONFIG_DEFAULT,
    REPORT_CONFIG_IMMEDIATE,
)
from zhaws.server.zigbee.cluster.util import parse_and_log_command

if TYPE_CHECKING:
    from zhaws.server.zigbee.endpoint import Endpoint


class LevelChangeEvent(BaseEvent):
    """Event to signal that a cluster attribute has been updated."""

    level: int
    event_type: Literal["cluster_handler_event"] = "cluster_handler_event"
    event: Literal["cluster_handler_move_level", "cluster_handler_set_level"]


@registries.CLUSTER_HANDLER_REGISTRY.register(general.Alarms.cluster_id)
class Alarms(ClusterHandler):
    """Alarms cluster handler."""


@registries.CLUSTER_HANDLER_REGISTRY.register(general.AnalogInput.cluster_id)
class AnalogInput(ClusterHandler):
    """Analog Input cluster handler."""

    REPORT_CONFIG = [{"attr": "present_value", "config": REPORT_CONFIG_DEFAULT}]


@registries.BINDABLE_CLUSTERS.register(general.AnalogOutput.cluster_id)
@registries.CLUSTER_HANDLER_REGISTRY.register(general.AnalogOutput.cluster_id)
class AnalogOutput(ClusterHandler):
    """Analog Output cluster handler."""

    REPORT_CONFIG = [{"attr": "present_value", "config": REPORT_CONFIG_DEFAULT}]
    ZCL_INIT_ATTRS = {
        "min_present_value": True,
        "max_present_value": True,
        "resolution": True,
        "relinquish_default": True,
        "description": True,
        "engineering_units": True,
        "application_type": True,
    }

    @property
    def present_value(self) -> float | None:
        """Return cached value of present_value."""
        return self.cluster.get("present_value")

    @property
    def min_present_value(self) -> float | None:
        """Return cached value of min_present_value."""
        return self.cluster.get("min_present_value")

    @property
    def max_present_value(self) -> float | None:
        """Return cached value of max_present_value."""
        return self.cluster.get("max_present_value")

    @property
    def resolution(self) -> float | None:
        """Return cached value of resolution."""
        return self.cluster.get("resolution")

    @property
    def relinquish_default(self) -> float | None:
        """Return cached value of relinquish_default."""
        return self.cluster.get("relinquish_default")

    @property
    def description(self) -> str | None:
        """Return cached value of description."""
        return self.cluster.get("description")

    @property
    def engineering_units(self) -> int | None:
        """Return cached value of engineering_units."""
        return self.cluster.get("engineering_units")

    @property
    def application_type(self) -> int | None:
        """Return cached value of application_type."""
        return self.cluster.get("application_type")

    async def async_set_present_value(self, value: float) -> bool:
        """Update present_value."""
        try:
            res = await self.cluster.write_attributes({"present_value": value})
        except zigpy.exceptions.ZigbeeException as ex:
            self.error("Could not set value: %s", ex)
            return False
        if isinstance(res, list) and all(
            record.status == Status.SUCCESS for record in res[0]
        ):
            return True
        return False


@registries.CLUSTER_HANDLER_REGISTRY.register(general.AnalogValue.cluster_id)
class AnalogValue(ClusterHandler):
    """Analog Value cluster handler."""

    REPORT_CONFIG = [{"attr": "present_value", "config": REPORT_CONFIG_DEFAULT}]


@registries.CLUSTER_HANDLER_REGISTRY.register(general.ApplianceControl.cluster_id)
class ApplianceContorl(ClusterHandler):
    """Appliance Control cluster handler."""


@registries.HANDLER_ONLY_CLUSTERS.register(general.Basic.cluster_id)
@registries.CLUSTER_HANDLER_REGISTRY.register(general.Basic.cluster_id)
class BasicClusterHandler(ClusterHandler):
    """Cluster handler to interact with the basic cluster."""

    UNKNOWN = 0
    BATTERY = 3
    BIND: bool = False

    POWER_SOURCES = {
        UNKNOWN: "Unknown",
        1: "Mains (single phase)",
        2: "Mains (3 phase)",
        BATTERY: "Battery",
        4: "DC source",
        5: "Emergency mains constantly powered",
        6: "Emergency mains and transfer switch",
    }


@registries.CLUSTER_HANDLER_REGISTRY.register(general.BinaryInput.cluster_id)
class BinaryInput(ClusterHandler):
    """Binary Input cluster handler."""

    REPORT_CONFIG = [{"attr": "present_value", "config": REPORT_CONFIG_DEFAULT}]


@registries.CLUSTER_HANDLER_REGISTRY.register(general.BinaryOutput.cluster_id)
class BinaryOutput(ClusterHandler):
    """Binary Output cluster handler."""

    REPORT_CONFIG = [{"attr": "present_value", "config": REPORT_CONFIG_DEFAULT}]


@registries.CLUSTER_HANDLER_REGISTRY.register(general.BinaryValue.cluster_id)
class BinaryValue(ClusterHandler):
    """Binary Value cluster handler."""

    REPORT_CONFIG = [{"attr": "present_value", "config": REPORT_CONFIG_DEFAULT}]


@registries.CLUSTER_HANDLER_REGISTRY.register(general.Commissioning.cluster_id)
class Commissioning(ClusterHandler):
    """Commissioning cluster handler."""


@registries.CLUSTER_HANDLER_REGISTRY.register(general.DeviceTemperature.cluster_id)
class DeviceTemperature(ClusterHandler):
    """Device Temperature cluster handler."""


@registries.CLUSTER_HANDLER_REGISTRY.register(general.GreenPowerProxy.cluster_id)
class GreenPowerProxy(ClusterHandler):
    """Green Power Proxy cluster handler."""

    BIND: bool = False


@registries.CLUSTER_HANDLER_REGISTRY.register(general.Groups.cluster_id)
class Groups(ClusterHandler):
    """Groups cluster handler."""

    BIND: bool = False


@registries.CLUSTER_HANDLER_REGISTRY.register(general.Identify.cluster_id)
class Identify(ClusterHandler):
    """Identify cluster handler."""

    BIND: bool = False

    def cluster_command(self, tsn: int, command_id: int, args: Any) -> None:
        """Handle commands received to this cluster."""
        # TODO cmd = parse_and_log_command(self, tsn, command_id, args)
        # TODO if cmd == "trigger_effect":
        # TODO self.send_event(f"{self.unique_id}_{cmd}", args[0])


@registries.CLIENT_CLUSTER_HANDLER_REGISTRY.register(general.LevelControl.cluster_id)
class LevelControlClientClusterHandler(ClientClusterHandler):
    """LevelControl client cluster handler."""


@registries.BINDABLE_CLUSTERS.register(general.LevelControl.cluster_id)
@registries.CLUSTER_HANDLER_REGISTRY.register(general.LevelControl.cluster_id)
class LevelControlClusterHandler(ClusterHandler):
    """Cluster handler for the LevelControl Zigbee cluster."""

    CURRENT_LEVEL = 0
    REPORT_CONFIG = [{"attr": "current_level", "config": REPORT_CONFIG_ASAP}]

    @property
    def current_level(self) -> int | None:
        """Return cached value of the current_level attribute."""
        return self.cluster.get("current_level")

    def cluster_command(self, tsn: int, command_id: int, args: Any) -> None:
        """Handle commands received to this cluster."""
        cmd = parse_and_log_command(self, tsn, command_id, args)

        if cmd in ("move_to_level", "move_to_level_with_on_off"):
            self.dispatch_level_change("set_level", args[0])
        elif cmd in ("move", "move_with_on_off"):
            # We should dim slowly -- for now, just step once
            rate = args[1]
            if args[0] == 0xFF:
                rate = 10  # Should read default move rate
            self.dispatch_level_change("move_level", -rate if args[0] else rate)
        elif cmd in ("step", "step_with_on_off"):
            # Step (technically may change on/off)
            self.dispatch_level_change("move_level", -args[1] if args[0] else args[1])

    def attribute_updated(self, attrid: int, value: Any) -> None:
        """Handle attribute updates on this cluster."""
        self.debug("received attribute: %s update with value: %s", attrid, value)
        if attrid == self.CURRENT_LEVEL:
            self.dispatch_level_change("set_level", value)
            pass

    def dispatch_level_change(self, command: str, level: int) -> None:
        """Dispatch level change."""
        self.emit(
            CLUSTER_HANDLER_EVENT,
            LevelChangeEvent(
                level=level,
                event=f"cluster_handler_{command}",
            ),
        )


@registries.CLUSTER_HANDLER_REGISTRY.register(general.MultistateInput.cluster_id)
class MultistateInput(ClusterHandler):
    """Multistate Input cluster handler."""

    REPORT_CONFIG = [{"attr": "present_value", "config": REPORT_CONFIG_DEFAULT}]


@registries.CLUSTER_HANDLER_REGISTRY.register(general.MultistateOutput.cluster_id)
class MultistateOutput(ClusterHandler):
    """Multistate Output cluster handler."""

    REPORT_CONFIG = [{"attr": "present_value", "config": REPORT_CONFIG_DEFAULT}]


@registries.CLUSTER_HANDLER_REGISTRY.register(general.MultistateValue.cluster_id)
class MultistateValue(ClusterHandler):
    """Multistate Value cluster handler."""

    REPORT_CONFIG = [{"attr": "present_value", "config": REPORT_CONFIG_DEFAULT}]


@registries.CLIENT_CLUSTER_HANDLER_REGISTRY.register(general.OnOff.cluster_id)
class OnOffClientClusterHandler(ClientClusterHandler):
    """OnOff client cluster handler."""


@registries.BINDABLE_CLUSTERS.register(general.OnOff.cluster_id)
@registries.CLUSTER_HANDLER_REGISTRY.register(general.OnOff.cluster_id)
class OnOffClusterHandler(ClusterHandler):
    """Cluster handler for the OnOff Zigbee cluster."""

    ON_OFF = 0
    REPORT_CONFIG = [{"attr": "on_off", "config": REPORT_CONFIG_IMMEDIATE}]

    def __init__(self, cluster: ZigpyClusterType, endpoint: Endpoint) -> None:
        """Initialize OnOffClusterHandler."""
        super().__init__(cluster, endpoint)
        self._state: bool | None = None
        self._off_listener: asyncio.TimerHandle | None = None

    @property
    def on_off(self) -> bool | None:
        """Return cached value of on/off attribute."""
        return self.cluster.get("on_off")

    def cluster_command(self, tsn: int, command_id: int, args: Any) -> None:
        """Handle commands received to this cluster."""
        cmd = parse_and_log_command(self, tsn, command_id, args)

        if cmd in ("off", "off_with_effect"):
            self.attribute_updated(self.ON_OFF, False)
        elif cmd in ("on", "on_with_recall_global_scene"):
            self.attribute_updated(self.ON_OFF, True)
        elif cmd == "on_with_timed_off":
            should_accept = args[0]
            on_time = args[1]
            # 0 is always accept 1 is only accept when already on
            if should_accept == 0 or (should_accept == 1 and self._state):
                if self._off_listener is not None:
                    self._off_listener.cancel()
                    self._off_listener = None
                self.attribute_updated(self.ON_OFF, True)
                if on_time > 0:
                    self._off_listener = asyncio.get_running_loop().call_later(
                        (on_time / 10),  # value is in 10ths of a second
                        self.set_to_off,
                    )
        elif cmd == "toggle":
            self.attribute_updated(self.ON_OFF, not bool(self._state))

    def set_to_off(self) -> None:
        """Set the state to off."""
        self._off_listener = None
        self.attribute_updated(self.ON_OFF, False)

    def attribute_updated(self, attrid: int, value: Any) -> None:
        """Handle attribute updates on this cluster."""
        if attrid == self.ON_OFF:
            self.emit(
                CLUSTER_HANDLER_EVENT,
                ClusterAttributeUpdatedEvent(
                    id=attrid,
                    name="on_off",
                    value=value,
                ),
            )
            self._state = bool(value)

    async def async_initialize_handler_specific(self, from_cache: bool) -> None:
        """Initialize cluster handler."""
        self._state = self.on_off

    async def async_update(self) -> None:
        """Initialize cluster handler."""
        if self.cluster.is_client:
            return
        from_cache = not self._endpoint.device.is_mains_powered
        self.debug("attempting to update onoff state - from cache: %s", from_cache)
        state = await self.get_attribute_value(self.ON_OFF, from_cache=from_cache)
        if state is not None:
            self._state = bool(state)
        await super().async_update()


@registries.CLUSTER_HANDLER_REGISTRY.register(general.OnOffConfiguration.cluster_id)
class OnOffConfiguration(ClusterHandler):
    """OnOff Configuration cluster handler."""


@registries.CLIENT_CLUSTER_HANDLER_REGISTRY.register(general.Ota.cluster_id)
@registries.CLUSTER_HANDLER_REGISTRY.register(general.Ota.cluster_id)
class Ota(ClusterHandler):
    """OTA cluster handler."""

    BIND: bool = False

    def cluster_command(
        self, tsn: int, command_id: int, args: list[Any] | None
    ) -> None:
        """Handle OTA commands."""
        cmd_name = self.cluster.server_commands.get(command_id, [command_id])[0]
        # TODO signal_id = self._ch_pool.unique_id.split("-")[0]
        if cmd_name == "query_next_image":
            """TODO
            self.send_event(SIGNAL_UPDATE_DEVICE.format(signal_id), args[3])
            """
            pass


@registries.CLUSTER_HANDLER_REGISTRY.register(general.Partition.cluster_id)
class Partition(ClusterHandler):
    """Partition cluster handler."""


@registries.HANDLER_ONLY_CLUSTERS.register(general.PollControl.cluster_id)
@registries.CLUSTER_HANDLER_REGISTRY.register(general.PollControl.cluster_id)
class PollControl(ClusterHandler):
    """Poll Control cluster handler."""

    CHECKIN_INTERVAL = 55 * 60 * 4  # 55min
    CHECKIN_FAST_POLL_TIMEOUT = 2 * 4  # 2s
    LONG_POLL = 6 * 4  # 6s
    _IGNORED_MANUFACTURER_ID = {
        4476,
    }  # IKEA

    async def async_configure_handler_specific(self) -> None:
        """Configure cluster handler: set check-in interval."""
        try:
            res = await self.cluster.write_attributes(
                {"checkin_interval": self.CHECKIN_INTERVAL}
            )
            self.debug("%ss check-in interval set: %s", self.CHECKIN_INTERVAL / 4, res)
        except (asyncio.TimeoutError, zigpy.exceptions.ZigbeeException) as ex:
            self.debug("Couldn't set check-in interval: %s", ex)

    def cluster_command(
        self, tsn: int, command_id: int, args: list[Any] | None
    ) -> None:
        """Handle commands received to this cluster."""
        cmd_name = self.cluster.client_commands.get(command_id, [command_id])[0]
        self.debug("Received %s tsn command '%s': %s", tsn, cmd_name, args)
        # TODO self.zha_send_event(cmd_name, args)
        if cmd_name == "checkin":
            self.cluster.create_catching_task(self.check_in_response(tsn))

    async def check_in_response(self, tsn: int) -> None:
        """Respond to checkin command."""
        await self.checkin_response(True, self.CHECKIN_FAST_POLL_TIMEOUT, tsn=tsn)
        if self._endpoint.device.manufacturer_code not in self._IGNORED_MANUFACTURER_ID:
            await self.set_long_poll_interval(self.LONG_POLL)
        await self.fast_poll_stop()

    def skip_manufacturer_id(self, manufacturer_code: int) -> None:
        """Block a specific manufacturer id from changing default polling."""
        self._IGNORED_MANUFACTURER_ID.add(manufacturer_code)


@registries.CLUSTER_HANDLER_REGISTRY.register(general.PowerConfiguration.cluster_id)
class PowerConfigurationClusterHandler(ClusterHandler):
    """Cluster handler for the zigbee power configuration cluster."""

    REPORT_CONFIG = [
        {"attr": "battery_voltage", "config": REPORT_CONFIG_BATTERY_SAVE},
        {"attr": "battery_percentage_remaining", "config": REPORT_CONFIG_BATTERY_SAVE},
    ]

    def async_initialize_handler_specific(self, from_cache: bool) -> Coroutine:
        """Initialize cluster handler specific attrs."""
        attributes = [
            "battery_size",
            "battery_quantity",
        ]
        return self.get_attributes(attributes, from_cache=from_cache)


@registries.CLUSTER_HANDLER_REGISTRY.register(general.PowerProfile.cluster_id)
class PowerProfile(ClusterHandler):
    """Power Profile cluster handler."""


@registries.CLUSTER_HANDLER_REGISTRY.register(general.RSSILocation.cluster_id)
class RSSILocation(ClusterHandler):
    """RSSI Location cluster handler."""


@registries.CLIENT_CLUSTER_HANDLER_REGISTRY.register(general.Scenes.cluster_id)
class ScenesClientClusterHandler(ClientClusterHandler):
    """Scenes cluster handler."""


@registries.CLUSTER_HANDLER_REGISTRY.register(general.Scenes.cluster_id)
class Scenes(ClusterHandler):
    """Scenes cluster handler."""


@registries.CLUSTER_HANDLER_REGISTRY.register(general.Time.cluster_id)
class Time(ClusterHandler):
    """Time cluster handler."""
