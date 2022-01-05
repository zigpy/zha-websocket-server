"""Number platform for zhawss."""

import functools

from zhawss.platforms import PlatformEntity
from zhawss.platforms.registries import PLATFORM_ENTITIES, Platform
from zhawss.zigbee.cluster.const import CLUSTER_HANDLER_ANALOG_INPUT

STRICT_MATCH = functools.partial(PLATFORM_ENTITIES.strict_match, Platform.NUMBER)


@STRICT_MATCH(cluster_handler_names=CLUSTER_HANDLER_ANALOG_INPUT)
class Number(PlatformEntity):
    """Representation of a zhawss number."""

    PLATFORM = Platform.LOCK
