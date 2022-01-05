"""Lock platform for zhawss."""

import functools

from zhawss.platforms import PlatformEntity
from zhawss.platforms.registries import PLATFORM_ENTITIES, Platform
from zhawss.zigbee.cluster.const import CLUSTER_HANDLER_DOORLOCK

MULTI_MATCH = functools.partial(PLATFORM_ENTITIES.multipass_match, Platform.LOCK)


@MULTI_MATCH(cluster_handler_names=CLUSTER_HANDLER_DOORLOCK)
class Lock(PlatformEntity):
    """Representation of a zhawss lock."""

    PLATFORM = Platform.LOCK
