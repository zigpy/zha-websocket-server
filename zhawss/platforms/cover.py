"""Cover platform for zhawss."""

import functools

from zhawss.platforms import PlatformEntity
from zhawss.platforms.registries import PLATFORM_ENTITIES, Platform
from zhawss.zigbee.cluster.const import (
    CLUSTER_HANDLER_COVER,
    CLUSTER_HANDLER_LEVEL,
    CLUSTER_HANDLER_ON_OFF,
    CLUSTER_HANDLER_SHADE,
)

MULTI_MATCH = functools.partial(PLATFORM_ENTITIES.multipass_match, Platform.COVER)


@MULTI_MATCH(cluster_handler_names=CLUSTER_HANDLER_COVER)
class Cover(PlatformEntity):
    """Representation of a zhawss cover."""

    PLATFORM = Platform.COVER


@MULTI_MATCH(
    cluster_handler_names={
        CLUSTER_HANDLER_LEVEL,
        CLUSTER_HANDLER_ON_OFF,
        CLUSTER_HANDLER_SHADE,
    }
)
class Shade(PlatformEntity):
    """ZHAWSS Shade."""

    PLATFORM = Platform.COVER


@MULTI_MATCH(
    cluster_handler_names={CLUSTER_HANDLER_LEVEL, CLUSTER_HANDLER_ON_OFF},
    manufacturers="Keen Home Inc",
)
class KeenVent(Shade):
    """Keen vent cover."""
