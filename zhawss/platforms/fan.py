"""Fan platform for zhawss."""

import functools

from zhawss.platforms import PlatformEntity
from zhawss.platforms.registries import PLATFORM_ENTITIES, Platform
from zhawss.zigbee.cluster.const import CLUSTER_HANDLER_FAN

STRICT_MATCH = functools.partial(PLATFORM_ENTITIES.strict_match, Platform.FAN)


@STRICT_MATCH(cluster_handler_names=CLUSTER_HANDLER_FAN)
class Fan(PlatformEntity):
    """Representation of a zhawss fan."""

    PLATFORM = Platform.FAN
