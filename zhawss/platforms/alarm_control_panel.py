"""Alarm control panel module for zhawss."""

import functools
from typing import Dict, Final, List, Union

from backports.strenum.strenum import StrEnum
from zigpy.zcl.clusters.security import IasAce

from zhawss.platforms import PlatformEntity
from zhawss.platforms.registries import PLATFORM_ENTITIES, Platform
from zhawss.zigbee.cluster.const import CLUSTER_HANDLER_IAS_ACE
from zhawss.zigbee.cluster.security import IasAce as IasAceClusterHandler
from zhawss.zigbee.cluster.types import ClusterHandlerType
from zhawss.zigbee.types import DeviceType, EndpointType

STRICT_MATCH = functools.partial(
    PLATFORM_ENTITIES.strict_match, Platform.ALARM_CONTROL_PANEL
)

SUPPORT_ALARM_ARM_HOME: Final = 1
SUPPORT_ALARM_ARM_AWAY: Final = 2
SUPPORT_ALARM_ARM_NIGHT: Final = 4
SUPPORT_ALARM_TRIGGER: Final = 8
SUPPORT_ALARM_ARM_CUSTOM_BYPASS: Final = 16
SUPPORT_ALARM_ARM_VACATION: Final = 32


class AlarmState(StrEnum):
    DISARMED = "disarmed"
    ARMED_HOME = "armed_home"
    ARMED_AWAY = "armed_away"
    ARMED_NIGHT = "armed_night"
    ARMED_VACATION = "armed_vacation"
    ARMED_CUSTOM_BYPASS = "armed_custom_bypass"
    PENDING = "pending"
    ARMING = "arming"
    DISARMING = "disarming"
    TRIGGERED = "triggered"


IAS_ACE_STATE_MAP = {
    IasAce.PanelStatus.Panel_Disarmed: AlarmState.DISARMED,
    IasAce.PanelStatus.Armed_Stay: AlarmState.ARMED_HOME,
    IasAce.PanelStatus.Armed_Night: AlarmState.ARMED_NIGHT,
    IasAce.PanelStatus.Armed_Away: AlarmState.ARMED_AWAY,
    IasAce.PanelStatus.In_Alarm: AlarmState.TRIGGERED,
}


@STRICT_MATCH(cluster_handler_names=CLUSTER_HANDLER_IAS_ACE)
class ZHAAlarmControlPanel(PlatformEntity):
    """Alarm Control Panel platform entity implementation."""

    PLATFORM = Platform.ALARM_CONTROL_PANEL

    def __init__(
        self,
        unique_id: str,
        cluster_handlers: List[ClusterHandlerType],
        endpoint: EndpointType,
        device: DeviceType,
    ):
        """Initialize the binary sensor."""
        super().__init__(unique_id, cluster_handlers, endpoint, device)
        self._cluster_handler: IasAceClusterHandler = cluster_handlers[0]
        self._cluster_handler.panel_code = "1234"
        self._cluster_handler.code_required_arm_actions = False
        self._cluster_handler.max_invalid_tries = 3

        """
        # TODO Once config / storage exist populate these values correctly
        self._channel.panel_code = async_get_zha_config_value(
            cfg_entry, ZHA_ALARM_OPTIONS, CONF_ALARM_MASTER_CODE, "1234"
        )
        self._channel.code_required_arm_actions = async_get_zha_config_value(
            cfg_entry, ZHA_ALARM_OPTIONS, CONF_ALARM_ARM_REQUIRES_CODE, False
        )
        self._channel.max_invalid_tries = async_get_zha_config_value(
            cfg_entry, ZHA_ALARM_OPTIONS, CONF_ALARM_FAILED_TRIES, 3
        )
        """
        self._cluster_handler.add_listener(self)

    def cluster_handler_state_changed(self):
        """Handle state changed on cluster."""
        self.send_state_changed_event()

    @property
    def code_arm_required(self):
        """Whether the code is required for arm actions."""
        return self._channel.code_required_arm_actions

    async def async_alarm_disarm(self, code=None):
        """Send disarm command."""
        self._channel.arm(IasAce.ArmMode.Disarm, code, 0)
        self.send_state_changed_event()

    async def async_alarm_arm_home(self, code=None):
        """Send arm home command."""
        self._channel.arm(IasAce.ArmMode.Arm_Day_Home_Only, code, 0)
        self.send_state_changed_event()

    async def async_alarm_arm_away(self, code=None):
        """Send arm away command."""
        self._channel.arm(IasAce.ArmMode.Arm_All_Zones, code, 0)
        self.send_state_changed_event()

    async def async_alarm_arm_night(self, code=None):
        """Send arm night command."""
        self._channel.arm(IasAce.ArmMode.Arm_Night_Sleep_Only, code, 0)
        self.send_state_changed_event()

    async def async_alarm_trigger(self, code=None):
        """Send alarm trigger command."""
        self.send_state_changed_event()

    @property
    def supported_features(self) -> int:
        """Return the list of supported features."""
        return (
            SUPPORT_ALARM_ARM_HOME
            | SUPPORT_ALARM_ARM_AWAY
            | SUPPORT_ALARM_ARM_NIGHT
            | SUPPORT_ALARM_TRIGGER
        )

    @property
    def state(self):
        """Return the state of the entity."""
        return IAS_ACE_STATE_MAP.get(self._cluster_handler.armed_state)

    def get_state(self) -> Union[str, Dict, None]:
        return self.state

    def to_json(self) -> dict:
        """Return a JSON representation of the alarm control panel."""
        json = super().to_json()
        json["supported_features"] = self.supported_features
        json[
            "code_required_arm_actions"
        ] = self._cluster_handler.code_required_arm_actions
        json["max_invalid_tries"] = self._cluster_handler.max_invalid_tries
        return json
