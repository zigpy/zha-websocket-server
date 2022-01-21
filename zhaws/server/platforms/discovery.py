"""Device discovery functions for Zigbee Home Automation."""
from __future__ import annotations

from collections import Counter
import logging
from typing import TYPE_CHECKING, Any

from zhaws.server.platforms import (  # noqa: F401 pylint: disable=unused-import,
    GroupEntity,
    alarm_control_panel,
    binary_sensor,
    button,
    climate,
    cover,
    device_tracker,
    fan,
    light,
    lock,
    number,
    select,
    sensor,
    siren,
    switch,
)
from zhaws.server.platforms.registries import (
    DEVICE_CLASS,
    PLATFORM_ENTITIES,
    REMOTE_DEVICE_TYPES,
    SINGLE_INPUT_CLUSTER_DEVICE_CLASS,
    SINGLE_OUTPUT_CLUSTER_DEVICE_CLASS,
    Platform,
)

if TYPE_CHECKING:
    from zhaws.server.websocket.server import Server
    from zhaws.server.zigbee.endpoint import Endpoint
    from zhaws.server.zigbee.group import Group
    from zhaws.server.zigbee.controller import Controller

from zhaws.server.zigbee.cluster import (  # noqa: F401
    ClusterHandler,
    closures,
    general,
    homeautomation,
    hvac,
    lighting,
    lightlink,
    manufacturerspecific,
    measurement,
    protocol,
    security,
    smartenergy,
)
from zhaws.server.zigbee.registries import (
    CLUSTER_HANDLER_REGISTRY,
    HANDLER_ONLY_CLUSTERS,
)

_LOGGER = logging.getLogger(__name__)


PLATFORMS = (
    Platform.ALARM_CONTROL_PANEL,
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.CLIMATE,
    Platform.COVER,
    Platform.DEVICE_TRACKER,
    Platform.FAN,
    Platform.LIGHT,
    Platform.LOCK,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.SIREN,
    Platform.SWITCH,
)

GROUP_PLATFORMS = (
    Platform.FAN,
    Platform.LIGHT,
    Platform.SWITCH,
)


class ProbeEndpoint:
    """All discovered cluster handlers and entities of an endpoint."""

    def __init__(self) -> None:
        """Initialize instance."""
        self._device_configs: dict[str, Any] = {}

    def discover_entities(self, endpoint: Endpoint) -> None:
        """Process an endpoint on a zigpy device."""
        self.discover_by_device_type(endpoint)
        self.discover_multi_entities(endpoint)
        self.discover_by_cluster_id(endpoint)
        PLATFORM_ENTITIES.clean_up()

    def discover_by_device_type(self, endpoint: Endpoint) -> None:
        """Process an endpoint on a zigpy device."""

        unique_id = endpoint.unique_id

        platform = None  # remove this when the below is uncommented
        """TODO
        platform = self._device_configs.get(unique_id, {}).get(ha_const.CONF_TYPE)
        """
        if platform is None:
            ep_profile_id = endpoint.zigpy_endpoint.profile_id
            ep_device_type = endpoint.zigpy_endpoint.device_type
            platform = DEVICE_CLASS[ep_profile_id].get(ep_device_type)

        if platform and platform in PLATFORMS:
            cluster_handlers = endpoint.unclaimed_cluster_handlers()
            platform_entity_class, claimed = PLATFORM_ENTITIES.get_entity(
                platform,
                endpoint.device.manufacturer,
                endpoint.device.model,
                cluster_handlers,
            )
            if platform_entity_class is None:
                return
            endpoint.claim_cluster_handlers(claimed)
            endpoint.async_new_entity(
                platform, platform_entity_class, unique_id, claimed
            )

    def discover_by_cluster_id(self, endpoint: Endpoint) -> None:
        """Process an endpoint on a zigpy device."""

        items = SINGLE_INPUT_CLUSTER_DEVICE_CLASS.items()
        single_input_clusters = {
            cluster_class: match
            for cluster_class, match in items
            if not isinstance(cluster_class, int)
        }
        remaining_cluster_handlers = endpoint.unclaimed_cluster_handlers()
        for cluster_handler in remaining_cluster_handlers:
            if cluster_handler.cluster.cluster_id in HANDLER_ONLY_CLUSTERS:
                endpoint.claim_cluster_handlers([cluster_handler])
                continue

            platform = SINGLE_INPUT_CLUSTER_DEVICE_CLASS.get(
                cluster_handler.cluster.cluster_id
            )
            if platform is None:
                for cluster_class, match in single_input_clusters.items():
                    if isinstance(cluster_handler.cluster, cluster_class):
                        platform = match
                        break
            if platform is not None:
                self.probe_single_cluster(platform, cluster_handler, endpoint)

        # until we can get rid off registries
        self.handle_on_off_output_cluster_exception(endpoint)

    @staticmethod
    def probe_single_cluster(
        platform: Platform,
        cluster_handler: ClusterHandler,
        endpoint: Endpoint,
    ) -> None:
        """Probe specified cluster for specific platform."""
        if platform is None or platform not in PLATFORMS:
            return
        cluster_handler_list = [cluster_handler]
        unique_id = f"{endpoint.unique_id}-{cluster_handler.cluster.cluster_id}"

        entity_class, claimed = PLATFORM_ENTITIES.get_entity(
            platform,
            endpoint.device.manufacturer,
            endpoint.device.model,
            cluster_handler_list,
        )
        if entity_class is None:
            return
        endpoint.claim_cluster_handlers(claimed)
        endpoint.async_new_entity(platform, entity_class, unique_id, claimed)

    def handle_on_off_output_cluster_exception(
        self,
        endpoint: Endpoint,
    ) -> None:
        """Process output clusters of the endpoint."""

        profile_id = endpoint.zigpy_endpoint.profile_id
        device_type = endpoint.zigpy_endpoint.device_type
        if device_type in REMOTE_DEVICE_TYPES.get(profile_id, []):
            return

        for cluster_id, cluster in endpoint.zigpy_endpoint.out_clusters.items():
            platform = SINGLE_OUTPUT_CLUSTER_DEVICE_CLASS.get(cluster.cluster_id)
            if platform is None:
                continue

            cluster_handler_class = CLUSTER_HANDLER_REGISTRY.get(
                cluster_id, ClusterHandler
            )
            cluster_handler = cluster_handler_class(cluster, endpoint)
            self.probe_single_cluster(platform, cluster_handler, endpoint)

    @staticmethod
    def discover_multi_entities(endpoint: Endpoint) -> None:
        """Process an endpoint on and discover multiple entities."""

        ep_profile_id = endpoint.zigpy_endpoint.profile_id
        ep_device_type = endpoint.zigpy_endpoint.device_type
        platform_by_dev_type = DEVICE_CLASS[ep_profile_id].get(ep_device_type)
        remaining_cluster_handlers = endpoint.unclaimed_cluster_handlers()

        matches, claimed = PLATFORM_ENTITIES.get_multi_entity(
            endpoint.device.manufacturer,
            endpoint.device.model,
            remaining_cluster_handlers,
        )

        endpoint.claim_cluster_handlers(claimed)
        for platform, ent_n_handler_list in matches.items():
            for entity_and_handler in ent_n_handler_list:
                _LOGGER.debug(
                    "'%s' platform -> '%s' using %s",
                    platform,
                    entity_and_handler.entity_class.__name__,
                    [ch.name for ch in entity_and_handler.claimed_cluster_handlers],
                )
        for platform, ent_n_handler_list in matches.items():
            for entity_and_handler in ent_n_handler_list:
                if platform == platform_by_dev_type:
                    # for well known device types, like thermostats we'll take only 1st class
                    endpoint.async_new_entity(
                        platform,
                        entity_and_handler.entity_class,
                        endpoint.unique_id,
                        entity_and_handler.claimed_cluster_handlers,
                    )
                    break
                first_ch = entity_and_handler.claimed_cluster_handlers[0]
                endpoint.async_new_entity(
                    platform,
                    entity_and_handler.entity_class,
                    f"{endpoint.unique_id}-{first_ch.cluster.cluster_id}",
                    entity_and_handler.claimed_cluster_handlers,
                )

    def initialize(self, server: Server) -> None:
        """Update device overrides config."""
        """TODO
        zha_config = server.data[zha_const.DATA_ZHA].get(zha_const.DATA_ZHA_CONFIG, {})
        if overrides := zha_config.get(zha_const.CONF_DEVICE_CONFIG):
            self._device_configs.update(overrides)
        """


class GroupProbe:
    """Determine the appropriate platform for a group"""

    def __init__(self) -> None:
        """Initialize instance."""
        self._server: Server | None = None

    def initialize(self, server: Server) -> None:
        """Initialize the group probe."""
        self._server = server

    def _reprobe_group(self, group_id: int) -> None:
        """Reprobe a group for entities after its members change."""
        assert self._server is not None
        controller: Controller = self._server.controller
        if (group := controller.groups.get(group_id)) is None:
            return
        self.discover_group_entities(group)

    def discover_group_entities(self, group: Group) -> None:
        """Process a group and create any entities that are needed."""
        _LOGGER.info("Probing group %s for entities", group.name)
        # only create a group entity if there are 2 or more members in a group
        if len(group.members) < 2:
            _LOGGER.debug(
                "Group: %s:0x%04x has less than 2 members - skipping entity discovery",
                group.name,
                group.group_id,
            )
            return

        assert self._server is not None
        entity_platforms = GroupProbe.determine_entity_platforms(self._server, group)

        if not entity_platforms:
            _LOGGER.info("No entity platforms discovered for group %s", group.name)
            return

        for platform in entity_platforms:
            entity_class = PLATFORM_ENTITIES.get_group_entity(platform)
            if entity_class is None:
                continue
            _LOGGER.info("Creating entity : %s for group %s", entity_class, group.name)
            entity_class(group)

    @staticmethod
    def determine_entity_platforms(server: Server, group: Group) -> list[Platform]:
        """Determine the entity platforms for this group."""
        entity_domains: list[Platform] = []
        all_platform_occurrences = []
        for member in group.members:
            if member.device.is_coordinator:
                continue
            entities = member.associated_entities
            all_platform_occurrences.extend(
                [
                    entity.PLATFORM
                    for entity in entities
                    if entity.PLATFORM in GROUP_PLATFORMS
                ]
            )
        if not all_platform_occurrences:
            return entity_domains
        # get all platforms we care about if there are more than 2 entities of this platform
        counts = Counter(all_platform_occurrences)
        entity_platforms = [
            platform[0] for platform in counts.items() if platform[1] >= 2
        ]
        _LOGGER.debug(
            "The entity platforms are: %s for group: %s:0x%04x",
            entity_platforms,
            group.name,
            group.group_id,
        )
        return entity_platforms


PROBE: ProbeEndpoint = ProbeEndpoint()
GROUP_PROBE: GroupProbe = GroupProbe()
