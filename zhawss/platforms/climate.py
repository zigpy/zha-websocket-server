"""Climate platform for zhawss."""

import functools

from zhawss.platforms import PlatformEntity
from zhawss.platforms.registries import PLATFORM_ENTITIES, Platform
from zhawss.zigbee.cluster.const import CLUSTER_HANDLER_FAN, CLUSTER_HANDLER_THERMOSTAT

STRICT_MATCH = functools.partial(PLATFORM_ENTITIES.strict_match, Platform.CLIMATE)
MULTI_MATCH = functools.partial(PLATFORM_ENTITIES.multipass_match, Platform.CLIMATE)


@MULTI_MATCH(
    cluster_handler_names=CLUSTER_HANDLER_THERMOSTAT,
    aux_cluster_handlers=CLUSTER_HANDLER_FAN,
    stop_on_match_group=CLUSTER_HANDLER_THERMOSTAT,
)
class Thermostat(PlatformEntity):

    PLATFORM = Platform.CLIMATE


@MULTI_MATCH(
    cluster_handler_names={CLUSTER_HANDLER_THERMOSTAT, "sinope_manufacturer_specific"},
    manufacturers="Sinope Technologies",
    stop_on_match_group=CLUSTER_HANDLER_THERMOSTAT,
)
class SinopeTechnologiesThermostat(Thermostat):
    """Sinope Technologies Thermostat."""


@MULTI_MATCH(
    cluster_handler_names=CLUSTER_HANDLER_THERMOSTAT,
    aux_cluster_handlers=CLUSTER_HANDLER_FAN,
    manufacturers="Zen Within",
    stop_on_match_group=CLUSTER_HANDLER_THERMOSTAT,
)
class ZenWithinThermostat(Thermostat):
    """Zen Within Thermostat implementation."""


@MULTI_MATCH(
    cluster_handler_names=CLUSTER_HANDLER_THERMOSTAT,
    aux_cluster_handlers=CLUSTER_HANDLER_FAN,
    manufacturers="Centralite",
    models={"3157100", "3157100-E"},
    stop_on_match_group=CLUSTER_HANDLER_THERMOSTAT,
)
class CentralitePearl(ZenWithinThermostat):
    """Centralite Pearl Thermostat implementation."""


@STRICT_MATCH(
    cluster_handler_names=CLUSTER_HANDLER_THERMOSTAT,
    manufacturers={
        "_TZE200_ckud7u2l",
        "_TZE200_ywdxldoj",
        "_TZE200_cwnjrr72",
        "_TZE200_b6wax7g0",
        "_TZE200_2atgpdho",
        "_TZE200_pvvbommb",
        "_TZE200_4eeyebrt",
        "_TYST11_ckud7u2l",
        "_TYST11_ywdxldoj",
        "_TYST11_cwnjrr72",
        "_TYST11_2atgpdho",
    },
)
class MoesThermostat(Thermostat):
    """Moes Thermostat implementation."""
