"""
Security cluster handlers module for zhawss.

For more details about this component, please refer to the documentation at
https://home-assistant.io/integrations/zha/
"""
from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any, Callable, Literal

from zigpy.exceptions import ZigbeeException
from zigpy.zcl import Cluster as ZigpyClusterType
from zigpy.zcl.clusters import security
from zigpy.zcl.clusters.security import IasAce as AceCluster

from zhaws.model import BaseEvent
from zhaws.server.zigbee import registries
from zhaws.server.zigbee.cluster import (
    CLUSTER_HANDLER_EVENT,
    ClusterHandler,
    ClusterHandlerStatus,
)

if TYPE_CHECKING:
    from zhaws.server.zigbee.endpoint import Endpoint

IAS_ACE_ARM = 0x0000  # ("arm", (t.enum8, t.CharacterString, t.uint8_t), False),
IAS_ACE_BYPASS = 0x0001  # ("bypass", (t.LVList(t.uint8_t), t.CharacterString), False),
IAS_ACE_EMERGENCY = 0x0002  # ("emergency", (), False),
IAS_ACE_FIRE = 0x0003  # ("fire", (), False),
IAS_ACE_PANIC = 0x0004  # ("panic", (), False),
IAS_ACE_GET_ZONE_ID_MAP = 0x0005  # ("get_zone_id_map", (), False),
IAS_ACE_GET_ZONE_INFO = 0x0006  # ("get_zone_info", (t.uint8_t,), False),
IAS_ACE_GET_PANEL_STATUS = 0x0007  # ("get_panel_status", (), False),
IAS_ACE_GET_BYPASSED_ZONE_LIST = 0x0008  # ("get_bypassed_zone_list", (), False),
IAS_ACE_GET_ZONE_STATUS = (
    0x0009  # ("get_zone_status", (t.uint8_t, t.uint8_t, t.Bool, t.bitmap16), False)
)
NAME = 0
SIGNAL_ARMED_STATE_CHANGED = "zha_armed_state_changed"
SIGNAL_ALARM_TRIGGERED = "zha_armed_triggered"

WARNING_DEVICE_MODE_STOP = 0
WARNING_DEVICE_MODE_BURGLAR = 1
WARNING_DEVICE_MODE_FIRE = 2
WARNING_DEVICE_MODE_EMERGENCY = 3
WARNING_DEVICE_MODE_POLICE_PANIC = 4
WARNING_DEVICE_MODE_FIRE_PANIC = 5
WARNING_DEVICE_MODE_EMERGENCY_PANIC = 6

WARNING_DEVICE_STROBE_NO = 0
WARNING_DEVICE_STROBE_YES = 1

WARNING_DEVICE_SOUND_LOW = 0
WARNING_DEVICE_SOUND_MEDIUM = 1
WARNING_DEVICE_SOUND_HIGH = 2
WARNING_DEVICE_SOUND_VERY_HIGH = 3

WARNING_DEVICE_STROBE_LOW = 0x00
WARNING_DEVICE_STROBE_MEDIUM = 0x01
WARNING_DEVICE_STROBE_HIGH = 0x02
WARNING_DEVICE_STROBE_VERY_HIGH = 0x03

WARNING_DEVICE_SQUAWK_MODE_ARMED = 0
WARNING_DEVICE_SQUAWK_MODE_DISARMED = 1

_LOGGER = logging.getLogger(__name__)


class ClusterHandlerStateChangedEvent(BaseEvent):
    """Event to signal that a cluster attribute has been updated."""

    event_type: Literal["cluster_handler_event"] = "cluster_handler_event"
    event: Literal["cluster_handler_state_changed"] = "cluster_handler_state_changed"


@registries.CLUSTER_HANDLER_REGISTRY.register(AceCluster.cluster_id)
class IasAce(ClusterHandler):
    """IAS Ancillary Control Equipment cluster handler."""

    def __init__(self, cluster: ZigpyClusterType, endpoint: Endpoint) -> None:
        """Initialize IAS Ancillary Control Equipment cluster handler."""
        super().__init__(cluster, endpoint)
        self.command_map: dict[int, Callable] = {
            IAS_ACE_ARM: self.arm,
            IAS_ACE_BYPASS: self._bypass,
            IAS_ACE_EMERGENCY: self._emergency,
            IAS_ACE_FIRE: self._fire,
            IAS_ACE_PANIC: self._panic,
            IAS_ACE_GET_ZONE_ID_MAP: self._get_zone_id_map,
            IAS_ACE_GET_ZONE_INFO: self._get_zone_info,
            IAS_ACE_GET_PANEL_STATUS: self._send_panel_status_response,
            IAS_ACE_GET_BYPASSED_ZONE_LIST: self._get_bypassed_zone_list,
            IAS_ACE_GET_ZONE_STATUS: self._get_zone_status,
        }
        self.arm_map: dict[AceCluster.ArmMode, Callable] = {
            AceCluster.ArmMode.Disarm: self._disarm,
            AceCluster.ArmMode.Arm_All_Zones: self._arm_away,
            AceCluster.ArmMode.Arm_Day_Home_Only: self._arm_day,
            AceCluster.ArmMode.Arm_Night_Sleep_Only: self._arm_night,
        }
        self.armed_state: AceCluster.PanelStatus = AceCluster.PanelStatus.Panel_Disarmed
        self.invalid_tries: int = 0

        # These will all be setup by the entity from zha configuration
        self.panel_code: str = "1234"
        self.code_required_arm_actions: bool = False
        self.max_invalid_tries: int = 3

        # where do we store this to handle restarts
        self.alarm_status: AceCluster.AlarmStatus = AceCluster.AlarmStatus.No_Alarm

    def cluster_command(self, tsn: int, command_id: int, args: Any) -> None:
        """Handle commands received to this cluster."""
        self.warning(
            "received command %s", self._cluster.server_commands.get(command_id)[NAME]
        )
        self.command_map[command_id](*args)

    def arm(self, arm_mode: int, code: str | None, zone_id: int) -> None:
        """Handle the IAS ACE arm command."""
        mode = AceCluster.ArmMode(arm_mode)

        """TODO figure out events
        self.zha_send_event(
            self._cluster.server_commands.get(IAS_ACE_ARM)[NAME],
            {
                "arm_mode": mode.value,
                "arm_mode_description": mode.name,
                "code": code,
                "zone_id": zone_id,
            },
        )
        """

        zigbee_reply = self.arm_map[mode](code)
        asyncio.create_task(zigbee_reply)

        if self.invalid_tries >= self.max_invalid_tries:
            self.alarm_status = AceCluster.AlarmStatus.Emergency
            self.armed_state = AceCluster.PanelStatus.In_Alarm
        self._send_panel_status_changed()

    def _disarm(self, code: str) -> asyncio.Future:
        """Test the code and disarm the panel if the code is correct."""
        if (
            code != self.panel_code
            and self.armed_state != AceCluster.PanelStatus.Panel_Disarmed
        ):
            self.warning("Invalid code supplied to IAS ACE")
            self.invalid_tries += 1
            zigbee_reply = self.arm_response(
                AceCluster.ArmNotification.Invalid_Arm_Disarm_Code
            )
        else:
            self.invalid_tries = 0
            if (
                self.armed_state == AceCluster.PanelStatus.Panel_Disarmed
                and self.alarm_status == AceCluster.AlarmStatus.No_Alarm
            ):
                self.warning("IAS ACE already disarmed")
                zigbee_reply = self.arm_response(
                    AceCluster.ArmNotification.Already_Disarmed
                )
            else:
                self.warning("Disarming all IAS ACE zones")
                zigbee_reply = self.arm_response(
                    AceCluster.ArmNotification.All_Zones_Disarmed
                )

            self.armed_state = AceCluster.PanelStatus.Panel_Disarmed
            self.alarm_status = AceCluster.AlarmStatus.No_Alarm
        return zigbee_reply

    def _arm_day(self, code: str) -> asyncio.Future:
        """Arm the panel for day / home zones."""
        return self._handle_arm(
            code,
            AceCluster.PanelStatus.Armed_Stay,
            AceCluster.ArmNotification.Only_Day_Home_Zones_Armed,
        )

    def _arm_night(self, code: str) -> asyncio.Future:
        """Arm the panel for night / sleep zones."""
        return self._handle_arm(
            code,
            AceCluster.PanelStatus.Armed_Night,
            AceCluster.ArmNotification.Only_Night_Sleep_Zones_Armed,
        )

    def _arm_away(self, code: str) -> asyncio.Future:
        """Arm the panel for away mode."""
        return self._handle_arm(
            code,
            AceCluster.PanelStatus.Armed_Away,
            AceCluster.ArmNotification.All_Zones_Armed,
        )

    def _handle_arm(
        self,
        code: str,
        panel_status: AceCluster.PanelStatus,
        armed_type: AceCluster.ArmNotification,
    ) -> asyncio.Future:
        """Arm the panel with the specified statuses."""
        if self.code_required_arm_actions and code != self.panel_code:
            self.warning("Invalid code supplied to IAS ACE")
            zigbee_reply = self.arm_response(
                AceCluster.ArmNotification.Invalid_Arm_Disarm_Code
            )
        else:
            self.warning("Arming all IAS ACE zones")
            self.armed_state = panel_status
            zigbee_reply = self.arm_response(armed_type)
        return zigbee_reply

    def _bypass(self, zone_list: Any, code: str) -> asyncio.Future:
        """Handle the IAS ACE bypass command."""
        """TODO figure out events
        self.zha_send_event(
            self._cluster.server_commands.get(IAS_ACE_BYPASS)[NAME],
            {"zone_list": zone_list, "code": code},
        )
        """

    def _emergency(self) -> asyncio.Future:
        """Handle the IAS ACE emergency command."""
        self._set_alarm(AceCluster.AlarmStatus.Emergency)

    def _fire(self) -> asyncio.Future:
        """Handle the IAS ACE fire command."""
        self._set_alarm(AceCluster.AlarmStatus.Fire)

    def _panic(self) -> asyncio.Future:
        """Handle the IAS ACE panic command."""
        self._set_alarm(AceCluster.AlarmStatus.Emergency_Panic)

    def _set_alarm(self, status: AceCluster.AlarmStatus) -> asyncio.Future:
        """Set the specified alarm status."""
        self.alarm_status = status
        self.armed_state = AceCluster.PanelStatus.In_Alarm
        self.emit(
            CLUSTER_HANDLER_EVENT,
            ClusterHandlerStateChangedEvent(),
        )
        self._send_panel_status_changed()

    def _get_zone_id_map(self) -> asyncio.Future:
        """Handle the IAS ACE zone id map command."""

    def _get_zone_info(self, zone_id: int) -> asyncio.Future:
        """Handle the IAS ACE zone info command."""

    def _send_panel_status_response(self) -> asyncio.Future:
        """Handle the IAS ACE panel status response command."""
        response = self.panel_status_response(
            self.armed_state,
            0x00,
            AceCluster.AudibleNotification.Default_Sound,
            self.alarm_status,
        )
        asyncio.create_task(response)

    def _send_panel_status_changed(self) -> asyncio.Future:
        """Handle the IAS ACE panel status changed command."""
        response = self.panel_status_changed(
            self.armed_state,
            0x00,
            AceCluster.AudibleNotification.Default_Sound,
            self.alarm_status,
        )
        asyncio.create_task(response)
        self.emit(
            CLUSTER_HANDLER_EVENT,
            ClusterHandlerStateChangedEvent(),
        )

    def _get_bypassed_zone_list(self) -> asyncio.Future:
        """Handle the IAS ACE bypassed zone list command."""

    def _get_zone_status(
        self,
        starting_zone_id: int,
        max_zone_ids: int,
        zone_status_mask_flag: int,
        zone_status_mask: int,
    ) -> asyncio.Future:
        """Handle the IAS ACE zone status command."""


@registries.HANDLER_ONLY_CLUSTERS.register(security.IasWd.cluster_id)
@registries.CLUSTER_HANDLER_REGISTRY.register(security.IasWd.cluster_id)
class IasWd(ClusterHandler):
    """IAS Warning Device cluster handler."""

    @staticmethod
    def set_bit(
        destination_value: int, destination_bit: int, source_value: int, source_bit: int
    ) -> int:
        """Set the specified bit in the value."""

        if IasWd.get_bit(source_value, source_bit):
            return destination_value | (1 << destination_bit)
        return destination_value

    @staticmethod
    def get_bit(value: int, bit: int) -> bool:
        """Get the specified bit from the value."""
        return (value & (1 << bit)) != 0

    async def issue_squawk(
        self,
        mode: int = WARNING_DEVICE_SQUAWK_MODE_ARMED,
        strobe: int = WARNING_DEVICE_STROBE_YES,
        squawk_level: int = WARNING_DEVICE_SOUND_HIGH,
    ) -> None:
        """Issue a squawk command.

        This command uses the WD capabilities to emit a quick audible/visible pulse called a
        "squawk". The squawk command has no effect if the WD is currently active
        (warning in progress).
        """
        value = 0
        value = IasWd.set_bit(value, 0, squawk_level, 0)
        value = IasWd.set_bit(value, 1, squawk_level, 1)

        value = IasWd.set_bit(value, 3, strobe, 0)

        value = IasWd.set_bit(value, 4, mode, 0)
        value = IasWd.set_bit(value, 5, mode, 1)
        value = IasWd.set_bit(value, 6, mode, 2)
        value = IasWd.set_bit(value, 7, mode, 3)

        await self.squawk(value)

    async def issue_start_warning(
        self,
        mode: int = WARNING_DEVICE_MODE_EMERGENCY,
        strobe: int = WARNING_DEVICE_STROBE_YES,
        siren_level: int = WARNING_DEVICE_SOUND_HIGH,
        warning_duration: int = 5,  # seconds
        strobe_duty_cycle: int = 0x00,
        strobe_intensity: int = WARNING_DEVICE_STROBE_HIGH,
    ) -> None:
        """Issue a start warning command.

        This command starts the WD operation. The WD alerts the surrounding area by audible
        (siren) and visual (strobe) signals.

        strobe_duty_cycle indicates the length of the flash cycle. This provides a means
        of varying the flash duration for different alarm types (e.g., fire, police, burglar).
        Valid range is 0-100 in increments of 10. All other values SHALL be rounded to the
        nearest valid value. Strobe SHALL calculate duty cycle over a duration of one second.
        The ON state SHALL precede the OFF state. For example, if Strobe Duty Cycle Field specifies
        “40,” then the strobe SHALL flash ON for 4/10ths of a second and then turn OFF for
        6/10ths of a second.
        """
        value = 0
        value = IasWd.set_bit(value, 0, siren_level, 0)
        value = IasWd.set_bit(value, 1, siren_level, 1)

        value = IasWd.set_bit(value, 2, strobe, 0)

        value = IasWd.set_bit(value, 4, mode, 0)
        value = IasWd.set_bit(value, 5, mode, 1)
        value = IasWd.set_bit(value, 6, mode, 2)
        value = IasWd.set_bit(value, 7, mode, 3)

        await self.start_warning(
            value, warning_duration, strobe_duty_cycle, strobe_intensity
        )


@registries.CLUSTER_HANDLER_REGISTRY.register(security.IasZone.cluster_id)
class IASZoneClusterHandler(ClusterHandler):
    """Cluster handler for the IASZone Zigbee cluster."""

    ZCL_INIT_ATTRS = {"zone_status": True, "zone_state": False, "zone_type": True}

    def cluster_command(self, tsn: int, command_id: int, args: Any) -> None:
        """Handle commands received to this cluster."""
        _LOGGER.info("received cluster_command: %s args: %s", command_id, args)
        if command_id == 0:
            self.attribute_updated(2, args[0])
        elif command_id == 1:
            self.debug("Enroll requested")
            res = self._cluster.enroll_response(0, 0)
            asyncio.create_task(res)

    async def async_configure(self) -> None:
        """Configure IAS device."""
        await self.get_attribute_value("zone_type", from_cache=False)
        if self._endpoint.device.skip_configuration:
            self.debug("skipping IASZoneClusterHandler configuration")
            return

        self.debug("started IASZoneClusterHandler configuration")

        await self.bind()
        ieee = self.cluster.endpoint.device.application.ieee

        try:
            res = await self._cluster.write_attributes({"cie_addr": ieee})
            self.debug(
                "wrote cie_addr: %s to '%s' cluster: %s",
                str(ieee),
                self._cluster.ep_attribute,
                res[0],
            )
        except ZigbeeException as ex:
            self.debug(
                "Failed to write cie_addr: %s to '%s' cluster: %s",
                str(ieee),
                self._cluster.ep_attribute,
                str(ex),
            )

        self.debug("Sending pro-active IAS enroll response")
        self._cluster.create_catching_task(self._cluster.enroll_response(0, 0))

        self._status = ClusterHandlerStatus.CONFIGURED
        self.debug("finished IASZoneClusterHandler configuration")

    def attribute_updated(self, attrid: int, value: Any) -> None:
        """Handle attribute updates on this cluster."""
        if attrid == 2:
            value = value & 3
            super().attribute_updated(attrid, value)
