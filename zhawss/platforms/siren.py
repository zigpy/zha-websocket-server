"""Siren platform for zhawss."""

import functools

from zhawss.platforms import PlatformEntity
from zhawss.platforms.registries import PLATFORM_ENTITIES, Platform
from zhawss.zigbee.cluster.const import CLUSTER_HANDLER_IAS_WD

MULTI_MATCH = functools.partial(PLATFORM_ENTITIES.multipass_match, Platform.SIREN)


@MULTI_MATCH(cluster_handler_names=CLUSTER_HANDLER_IAS_WD)
class Siren(PlatformEntity):
    """Representation of a zhawss siren."""

    PLATFORM = Platform.SIREN
