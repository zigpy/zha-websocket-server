"""Alarm control panel module for zhawss."""

import functools

from zhawss.platforms import PlatformEntity
from zhawss.platforms.registries import PLATFORM_ENTITIES, Platform
from zhawss.zigbee.cluster.const import CLUSTER_HANDLER_IAS_ACE

STRICT_MATCH = functools.partial(
    PLATFORM_ENTITIES.strict_match, Platform.ALARM_CONTROL_PANEL
)


@STRICT_MATCH(cluster_handler_names=CLUSTER_HANDLER_IAS_ACE)
class ZHAAlarmControlPanel(PlatformEntity):
    """Alarm Control Panel platform entity implementation."""

    PLATFORM = Platform.ALARM_CONTROL_PANEL
