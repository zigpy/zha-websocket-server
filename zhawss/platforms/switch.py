"""Switch platform for zhawss."""

import functools

from zhawss.platforms import PlatformEntity
from zhawss.platforms.registries import PLATFORM_ENTITIES, Platform
from zhawss.zigbee.cluster.const import CLUSTER_HANDLER_ON_OFF

STRICT_MATCH = functools.partial(PLATFORM_ENTITIES.strict_match, Platform.SWITCH)


@STRICT_MATCH(cluster_handler_names=CLUSTER_HANDLER_ON_OFF)
class Switch(PlatformEntity):

    PLATFORM = Platform.SWITCH
