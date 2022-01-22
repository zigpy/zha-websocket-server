"""Mapping registries for zhawss."""
from __future__ import annotations

import collections
from collections.abc import Callable
import dataclasses
from typing import TYPE_CHECKING, Iterable, Type

import attr
from zigpy import zcl
import zigpy.profiles.zha
import zigpy.profiles.zll
from zigpy.types.named import EUI64

# importing cluster handlers updates registries
from zhaws.server.zigbee import (  # noqa: F401 pylint: disable=unused-import
    cluster as zha_cluster_handlers,
)

if TYPE_CHECKING:
    from zhaws.server.platforms import PlatformEntity
    from zhaws.server.zigbee.cluster import ClusterHandler
    from zhaws.server.platforms import GroupEntity

from zhaws.backports.enum import StrEnum


class Platform(StrEnum):
    """Available entity platforms."""

    AIR_QUALITY = "air_quality"
    ALARM_CONTROL_PANEL = "alarm_control_panel"
    BINARY_SENSOR = "binary_sensor"
    BUTTON = "button"
    CALENDAR = "calendar"
    CAMERA = "camera"
    CLIMATE = "climate"
    COVER = "cover"
    DEVICE_TRACKER = "device_tracker"
    FAN = "fan"
    GEO_LOCATION = "geo_location"
    HUMIDIFIER = "humidifier"
    IMAGE_PROCESSING = "image_processing"
    LIGHT = "light"
    LOCK = "lock"
    MAILBOX = "mailbox"
    MEDIA_PLAYER = "media_player"
    NOTIFY = "notify"
    NUMBER = "number"
    REMOTE = "remote"
    SCENE = "scene"
    SELECT = "select"
    SENSOR = "sensor"
    SIREN = "siren"
    STT = "stt"
    SWITCH = "switch"
    TTS = "tts"
    UNKNOWN = "unknown"
    VACUUM = "vacuum"
    WATER_HEATER = "water_heater"
    WEATHER = "weather"


GROUP_ENTITY_DOMAINS = [Platform.LIGHT, Platform.SWITCH, Platform.FAN]

SMARTTHINGS_ARRIVAL_SENSOR_DEVICE_TYPE = 0x8000

REMOTE_DEVICE_TYPES = {
    zigpy.profiles.zha.PROFILE_ID: [
        zigpy.profiles.zha.DeviceType.COLOR_CONTROLLER,
        zigpy.profiles.zha.DeviceType.COLOR_DIMMER_SWITCH,
        zigpy.profiles.zha.DeviceType.COLOR_SCENE_CONTROLLER,
        zigpy.profiles.zha.DeviceType.DIMMER_SWITCH,
        zigpy.profiles.zha.DeviceType.LEVEL_CONTROL_SWITCH,
        zigpy.profiles.zha.DeviceType.NON_COLOR_CONTROLLER,
        zigpy.profiles.zha.DeviceType.NON_COLOR_SCENE_CONTROLLER,
        zigpy.profiles.zha.DeviceType.ON_OFF_SWITCH,
        zigpy.profiles.zha.DeviceType.ON_OFF_LIGHT_SWITCH,
        zigpy.profiles.zha.DeviceType.REMOTE_CONTROL,
        zigpy.profiles.zha.DeviceType.SCENE_SELECTOR,
    ],
    zigpy.profiles.zll.PROFILE_ID: [
        zigpy.profiles.zll.DeviceType.COLOR_CONTROLLER,
        zigpy.profiles.zll.DeviceType.COLOR_SCENE_CONTROLLER,
        zigpy.profiles.zll.DeviceType.CONTROL_BRIDGE,
        zigpy.profiles.zll.DeviceType.CONTROLLER,
        zigpy.profiles.zll.DeviceType.SCENE_CONTROLLER,
    ],
}
REMOTE_DEVICE_TYPES = collections.defaultdict(list, REMOTE_DEVICE_TYPES)

SINGLE_INPUT_CLUSTER_DEVICE_CLASS = {
    # this works for now but if we hit conflicts we can break it out to
    # a different dict that is keyed by manufacturer
    zcl.clusters.general.AnalogOutput.cluster_id: Platform.NUMBER,
    zcl.clusters.general.MultistateInput.cluster_id: Platform.SENSOR,
    zcl.clusters.general.OnOff.cluster_id: Platform.SWITCH,
    zcl.clusters.hvac.Fan.cluster_id: Platform.FAN,
}

SINGLE_OUTPUT_CLUSTER_DEVICE_CLASS = {
    zcl.clusters.general.OnOff.cluster_id: Platform.BINARY_SENSOR,
    zcl.clusters.security.IasAce.cluster_id: Platform.ALARM_CONTROL_PANEL,
}

DEVICE_CLASS = {
    zigpy.profiles.zha.PROFILE_ID: {
        SMARTTHINGS_ARRIVAL_SENSOR_DEVICE_TYPE: Platform.DEVICE_TRACKER,
        zigpy.profiles.zha.DeviceType.THERMOSTAT: Platform.CLIMATE,
        zigpy.profiles.zha.DeviceType.COLOR_DIMMABLE_LIGHT: Platform.LIGHT,
        zigpy.profiles.zha.DeviceType.COLOR_TEMPERATURE_LIGHT: Platform.LIGHT,
        zigpy.profiles.zha.DeviceType.DIMMABLE_BALLAST: Platform.LIGHT,
        zigpy.profiles.zha.DeviceType.DIMMABLE_LIGHT: Platform.LIGHT,
        zigpy.profiles.zha.DeviceType.DIMMABLE_PLUG_IN_UNIT: Platform.LIGHT,
        zigpy.profiles.zha.DeviceType.EXTENDED_COLOR_LIGHT: Platform.LIGHT,
        zigpy.profiles.zha.DeviceType.LEVEL_CONTROLLABLE_OUTPUT: Platform.COVER,
        zigpy.profiles.zha.DeviceType.ON_OFF_BALLAST: Platform.SWITCH,
        zigpy.profiles.zha.DeviceType.ON_OFF_LIGHT: Platform.LIGHT,
        zigpy.profiles.zha.DeviceType.ON_OFF_PLUG_IN_UNIT: Platform.SWITCH,
        zigpy.profiles.zha.DeviceType.SHADE: Platform.COVER,
        zigpy.profiles.zha.DeviceType.SMART_PLUG: Platform.SWITCH,
        zigpy.profiles.zha.DeviceType.IAS_ANCILLARY_CONTROL: Platform.ALARM_CONTROL_PANEL,
        zigpy.profiles.zha.DeviceType.IAS_WARNING_DEVICE: Platform.SIREN,
    },
    zigpy.profiles.zll.PROFILE_ID: {
        zigpy.profiles.zll.DeviceType.COLOR_LIGHT: Platform.LIGHT,
        zigpy.profiles.zll.DeviceType.COLOR_TEMPERATURE_LIGHT: Platform.LIGHT,
        zigpy.profiles.zll.DeviceType.DIMMABLE_LIGHT: Platform.LIGHT,
        zigpy.profiles.zll.DeviceType.DIMMABLE_PLUGIN_UNIT: Platform.LIGHT,
        zigpy.profiles.zll.DeviceType.EXTENDED_COLOR_LIGHT: Platform.LIGHT,
        zigpy.profiles.zll.DeviceType.ON_OFF_LIGHT: Platform.LIGHT,
        zigpy.profiles.zll.DeviceType.ON_OFF_PLUGIN_UNIT: Platform.SWITCH,
    },
}
DEVICE_CLASS = collections.defaultdict(dict, DEVICE_CLASS)


def set_or_callable(
    value: str | Callable | Iterable | None,
) -> frozenset[str] | Callable:
    """Convert single str or None to a set. Pass through callables and sets."""
    if value is None:
        return frozenset()
    elif isinstance(value, str):
        return frozenset([value])
    elif callable(value):
        return value
    else:
        return frozenset(value)


@attr.s(frozen=True)
class MatchRule:
    """Match a ZHA Entity to a cluster handler name or generic id."""

    cluster_handler_names: frozenset = attr.ib(
        factory=frozenset, converter=set_or_callable
    )
    generic_ids: frozenset = attr.ib(factory=frozenset, converter=set_or_callable)
    manufacturers: frozenset | Callable = attr.ib(
        factory=frozenset, converter=set_or_callable
    )
    models: frozenset | Callable = attr.ib(factory=frozenset, converter=set_or_callable)
    aux_cluster_handlers: frozenset = attr.ib(
        factory=frozenset, converter=set_or_callable
    )

    @property
    def weight(self) -> int:
        """Return the weight of the matching rule.

        Most specific matches should be preferred over less specific. Model matching
        rules have a priority over manufacturer matching rules and rules matching a
        single model/manufacturer get a better priority over rules matching multiple
        models/manufacturers. And any model or manufacturers matching rules get better
        priority over rules matching only cluster handlers.
        But in case of a cluster handler name/handler id matching, we give rules matching
        multiple handlers a better priority over rules matching a single cluster handler.
        """
        weight = 0
        if self.models:
            weight += 401 - (1 if callable(self.models) else len(self.models))

        if self.manufacturers:
            weight += 301 - (
                1 if callable(self.manufacturers) else len(self.manufacturers)
            )

        weight += 10 * len(self.cluster_handler_names)
        weight += 5 * len(self.generic_ids)
        weight += 1 * len(self.aux_cluster_handlers)
        return weight

    def claim_cluster_handlers(
        self, endpoint: list[ClusterHandler]
    ) -> list[ClusterHandler]:
        """Return a list of cluster handlers this rule matches + aux cluster handlers."""
        claimed = []
        if isinstance(self.cluster_handler_names, frozenset):
            claimed.extend(
                [ch for ch in endpoint if ch.name in self.cluster_handler_names]
            )
        if isinstance(self.generic_ids, frozenset):
            claimed.extend([ch for ch in endpoint if ch.generic_id in self.generic_ids])
        if isinstance(self.aux_cluster_handlers, frozenset):
            claimed.extend(
                [ch for ch in endpoint if ch.name in self.aux_cluster_handlers]
            )
        return claimed

    def strict_matched(
        self, manufacturer: str, model: str, cluster_handlers: list[ClusterHandler]
    ) -> bool:
        """Return True if this device matches the criteria."""
        return all(self._matched(manufacturer, model, cluster_handlers))

    def loose_matched(
        self, manufacturer: str, model: str, cluster_handlers: list[ClusterHandler]
    ) -> bool:
        """Return True if this device matches the criteria."""
        return any(self._matched(manufacturer, model, cluster_handlers))

    def _matched(
        self, manufacturer: str, model: str, cluster_handlers: list[ClusterHandler]
    ) -> list[bool]:
        """Return a list of field matches."""
        if not any(attr.asdict(self).values()):
            return [False]

        matches = []
        if self.cluster_handler_names:
            cluster_handler_names = {ch.name for ch in cluster_handlers}
            matches.append(self.cluster_handler_names.issubset(cluster_handler_names))

        if self.generic_ids:
            all_generic_ids = {ch.generic_id for ch in cluster_handlers}
            matches.append(self.generic_ids.issubset(all_generic_ids))

        if self.manufacturers:
            if callable(self.manufacturers):
                matches.append(self.manufacturers(manufacturer))
            else:
                matches.append(manufacturer in self.manufacturers)

        if self.models:
            if callable(self.models):
                matches.append(self.models(model))
            else:
                matches.append(model in self.models)

        return matches


@dataclasses.dataclass
class EntityClassAndClusterHandlers:
    """Container for entity class and corresponding cluster handlers."""

    entity_class: Type[PlatformEntity]
    claimed_cluster_handlers: list[ClusterHandler]


class ZHAEntityRegistry:
    """Cluster handler to ZHA Entity mapping."""

    def __init__(self) -> None:
        """Initialize Registry instance."""
        self._strict_registry: dict[
            str, dict[MatchRule, Type[PlatformEntity]]
        ] = collections.defaultdict(dict)
        self._multi_entity_registry: dict[
            str, dict[int | str | None, dict[MatchRule, list[Type[PlatformEntity]]]]
        ] = collections.defaultdict(
            lambda: collections.defaultdict(lambda: collections.defaultdict(list))
        )
        self._group_registry: dict[str, Type[GroupEntity]] = {}
        self.single_device_matches: dict[
            Platform, dict[EUI64, list[str]]
        ] = collections.defaultdict(lambda: collections.defaultdict(list))

    def get_entity(
        self,
        platform: str,
        manufacturer: str,
        model: str,
        cluster_handlers: list[ClusterHandler],
        default: Type[PlatformEntity] | None = None,
    ) -> tuple[Type[PlatformEntity] | None, list[ClusterHandler]]:
        """Match cluster handlers to a ZHA Entity class."""
        matches = self._strict_registry[platform]
        for match in sorted(matches, key=lambda x: x.weight, reverse=True):
            if match.strict_matched(manufacturer, model, cluster_handlers):
                claimed = match.claim_cluster_handlers(cluster_handlers)
                return self._strict_registry[platform][match], claimed

        return default, []

    def get_multi_entity(
        self,
        manufacturer: str,
        model: str,
        cluster_handlers: list[ClusterHandler],
    ) -> tuple[dict[str, list[EntityClassAndClusterHandlers]], list[ClusterHandler]]:
        """Match ZHA cluster handlers to potentially multiple ZHA Entity classes."""
        result: dict[
            str, list[EntityClassAndClusterHandlers]
        ] = collections.defaultdict(list)
        all_claimed: set[ClusterHandler] = set()
        for platform, stop_match_groups in self._multi_entity_registry.items():
            for stop_match_grp, matches in stop_match_groups.items():
                sorted_matches = sorted(matches, key=lambda x: x.weight, reverse=True)
                for match in sorted_matches:
                    if match.strict_matched(manufacturer, model, cluster_handlers):
                        claimed = match.claim_cluster_handlers(cluster_handlers)
                        for ent_class in stop_match_groups[stop_match_grp][match]:
                            ent_n_cluster_handlers = EntityClassAndClusterHandlers(
                                ent_class, claimed
                            )
                            result[platform].append(ent_n_cluster_handlers)
                        all_claimed |= set(claimed)
                        if stop_match_grp:
                            break

        return result, list(all_claimed)

    def get_group_entity(self, platform: str) -> Type[GroupEntity] | None:
        """Match a ZHA group to a ZHA Entity class."""
        return self._group_registry.get(platform)

    def strict_match(
        self,
        platform: str,
        cluster_handler_names: set[str] | str | None = None,
        generic_ids: set[str] | str | None = None,
        manufacturers: Callable | set[str] | str | None = None,
        models: Callable | set[str] | str | None = None,
        aux_cluster_handlers: Callable | set[str] | str | None = None,
    ) -> Callable[[Type[PlatformEntity]], Type[PlatformEntity]]:
        """Decorate a strict match rule."""

        rule = MatchRule(
            cluster_handler_names,
            generic_ids,
            manufacturers,
            models,
            aux_cluster_handlers,
        )

        def decorator(zha_ent: Type[PlatformEntity]) -> Type[PlatformEntity]:
            """Register a strict match rule.

            All non empty fields of a match rule must match.
            """
            self._strict_registry[platform][rule] = zha_ent
            return zha_ent

        return decorator

    def multipass_match(
        self,
        platform: str,
        cluster_handler_names: set[str] | str | None = None,
        generic_ids: set[str] | str | None = None,
        manufacturers: Callable | set[str] | str | None = None,
        models: Callable | set[str] | str | None = None,
        aux_cluster_handlers: Callable | set[str] | str | None = None,
        stop_on_match_group: int | str | None = None,
    ) -> Callable[[Type[PlatformEntity]], Type[PlatformEntity]]:
        """Decorate a loose match rule."""

        rule = MatchRule(
            cluster_handler_names,
            generic_ids,
            manufacturers,
            models,
            aux_cluster_handlers,
        )

        def decorator(zha_entity: Type[PlatformEntity]) -> Type[PlatformEntity]:
            """Register a loose match rule.

            All non empty fields of a match rule must match.
            """
            # group the rules by cluster handlers
            self._multi_entity_registry[platform][stop_on_match_group][rule].append(
                zha_entity
            )
            return zha_entity

        return decorator

    def group_match(
        self, platform: str
    ) -> Callable[[Type[GroupEntity]], Type[GroupEntity]]:
        """Decorate a group match rule."""

        def decorator(zha_ent: Type[GroupEntity]) -> Type[GroupEntity]:
            """Register a group match rule."""
            self._group_registry[platform] = zha_ent
            return zha_ent

        return decorator

    def prevent_entity_creation(
        self, platform: Platform, ieee: EUI64, key: str
    ) -> bool:
        """Return True if the entity should not be created."""
        platform_restrictions = self.single_device_matches[platform]
        device_restrictions = platform_restrictions[ieee]
        if key in device_restrictions:
            return True
        device_restrictions.append(key)
        return False

    def clean_up(self) -> None:
        """Clean up post discovery."""
        self.single_device_matches.clear()


PLATFORM_ENTITIES = ZHAEntityRegistry()
