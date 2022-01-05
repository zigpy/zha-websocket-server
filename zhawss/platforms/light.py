"""Light platform for zhawss."""

import functools

from zhawss.platforms import PlatformEntity
from zhawss.platforms.registries import PLATFORM_ENTITIES, Platform
from zhawss.zigbee.cluster.const import (
    CLUSTER_HANDLER_COLOR,
    CLUSTER_HANDLER_LEVEL,
    CLUSTER_HANDLER_ON_OFF,
)

STRICT_MATCH = functools.partial(PLATFORM_ENTITIES.strict_match, Platform.LIGHT)


@STRICT_MATCH(
    cluster_handler_names=CLUSTER_HANDLER_ON_OFF,
    aux_cluster_handlers={CLUSTER_HANDLER_COLOR, CLUSTER_HANDLER_LEVEL},
)
class Light(PlatformEntity):
    """Representation of a light for zhawss."""

    PLATFORM = Platform.LIGHT


@STRICT_MATCH(
    cluster_handler_names=CLUSTER_HANDLER_ON_OFF,
    aux_cluster_handlers={CLUSTER_HANDLER_COLOR, CLUSTER_HANDLER_LEVEL},
    manufacturers={"Philips", "Signify Netherlands B.V."},
)
class HueLight(Light):
    """Representation of a HUE light which does not report attributes."""


@STRICT_MATCH(
    cluster_handler_names=CLUSTER_HANDLER_ON_OFF,
    aux_cluster_handlers={CLUSTER_HANDLER_COLOR, CLUSTER_HANDLER_LEVEL},
    manufacturers={"Jasco", "Quotra-Vision"},
)
class ForceOnLight(Light):
    """Representation of a light which does not respect move_to_level_with_on_off."""
