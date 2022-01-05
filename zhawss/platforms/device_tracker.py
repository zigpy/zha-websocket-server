"""Device Tracker platform for zhawss."""

import functools

from zhawss.platforms import PlatformEntity
from zhawss.platforms.registries import PLATFORM_ENTITIES, Platform
from zhawss.zigbee.cluster.const import CLUSTER_HANDLER_POWER_CONFIGURATION

STRICT_MATCH = functools.partial(
    PLATFORM_ENTITIES.strict_match, Platform.DEVICE_TRACKER
)


@STRICT_MATCH(cluster_handler_names=CLUSTER_HANDLER_POWER_CONFIGURATION)
class DeviceTracker(PlatformEntity):
    """Representation of a zhawss device tracker."""

    PLATFORM = Platform.DEVICE_TRACKER
