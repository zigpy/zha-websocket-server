"""Device discovery functions for Zigbee Home Automation."""
from __future__ import annotations

import logging

from zhaws.server.platforms import (  # noqa: F401 pylint: disable=unused-import,
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
from zhaws.server.websocket.types import ServerType
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
from zhaws.server.zigbee.cluster.types import ClusterHandlerType
from zhaws.server.zigbee.registries import (
    CLUSTER_HANDLER_REGISTRY,
    HANDLER_ONLY_CLUSTERS,
)
from zhaws.server.zigbee.types import EndpointType

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


class ProbeEndpoint:
    """All discovered cluster handlers and entities of an endpoint."""

    def __init__(self):
        """Initialize instance."""
        self._device_configs = {}

    def discover_entities(self, endpoint: EndpointType) -> None:
        """Process an endpoint on a zigpy device."""
        self.discover_by_device_type(endpoint)
        self.discover_multi_entities(endpoint)
        self.discover_by_cluster_id(endpoint)
        PLATFORM_ENTITIES.clean_up()

    def discover_by_device_type(self, endpoint: EndpointType) -> None:
        """Process an endpoint on a zigpy device."""

        unique_id = endpoint.unique_id

        platform = None  # remove this when the below is uncommented
        """TODO
        component = self._device_configs.get(unique_id, {}).get(ha_const.CONF_TYPE)
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

    def discover_by_cluster_id(self, endpoint: EndpointType) -> None:
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

            self.probe_single_cluster(platform, cluster_handler, endpoint)

        # until we can get rid off registries
        self.handle_on_off_output_cluster_exception(endpoint)

    @staticmethod
    def probe_single_cluster(
        platform: Platform,
        cluster_handler: ClusterHandlerType,
        endpoint: EndpointType,
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
        endpoint: EndpointType,
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
    def discover_multi_entities(endpoint: EndpointType) -> None:
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

    def initialize(self, server: ServerType) -> None:
        """Update device overrides config."""
        """TODO
        zha_config = server.data[zha_const.DATA_ZHA].get(zha_const.DATA_ZHA_CONFIG, {})
        if overrides := zha_config.get(zha_const.CONF_DEVICE_CONFIG):
            self._device_configs.update(overrides)
        """


"""TODO
class GroupProbe:
    # Determine the appropriate component for a group.

    def __init__(self):
        # Initialize instance.
        self._hass = None
        self._unsubs = []

    def initialize(self, hass: HomeAssistant) -> None:
        # Initialize the group probe.
        self._hass = hass
        self._unsubs.append(
            async_dispatcher_connect(
                hass, zha_const.SIGNAL_GROUP_ENTITY_REMOVED, self._reprobe_group
            )
        )

    def cleanup(self):
        # Clean up on when zha shuts down.
        for unsub in self._unsubs[:]:
            unsub()
            self._unsubs.remove(unsub)

    def _reprobe_group(self, group_id: int) -> None:
        # Reprobe a group for entities after its members change.
        zha_gateway = self._hass.data[zha_const.DATA_ZHA][zha_const.DATA_ZHA_GATEWAY]
        if (zha_group := zha_gateway.groups.get(group_id)) is None:
            return
        self.discover_group_entities(zha_group)

    def discover_group_entities(self, group: zha_typing.ZhaGroupType) -> None:
        # Process a group and create any entities that are needed.
        # only create a group entity if there are 2 or more members in a group
        if len(group.members) < 2:
            _LOGGER.debug(
                "Group: %s:0x%04x has less than 2 members - skipping entity discovery",
                group.name,
                group.group_id,
            )
            return

        entity_domains = GroupProbe.determine_entity_domains(self._hass, group)

        if not entity_domains:
            return

        zha_gateway = self._hass.data[zha_const.DATA_ZHA][zha_const.DATA_ZHA_GATEWAY]
        for domain in entity_domains:
            entity_class = zha_regs.ZHA_ENTITIES.get_group_entity(domain)
            if entity_class is None:
                continue
            self._hass.data[zha_const.DATA_ZHA][domain].append(
                (
                    entity_class,
                    (
                        group.get_domain_entity_ids(domain),
                        f"{domain}_zha_group_0x{group.group_id:04x}",
                        group.group_id,
                        zha_gateway.coordinator_zha_device,
                    ),
                )
            )
        async_dispatcher_send(self._hass, zha_const.SIGNAL_ADD_ENTITIES)

    @staticmethod
    def determine_entity_domains(
        hass: HomeAssistant, group: zha_typing.ZhaGroupType
    ) -> list[str]:
        # Determine the entity domains for this group.
        entity_domains: list[str] = []
        zha_gateway = hass.data[zha_const.DATA_ZHA][zha_const.DATA_ZHA_GATEWAY]
        all_domain_occurrences = []
        for member in group.members:
            if member.device.is_coordinator:
                continue
            entities = async_entries_for_device(
                zha_gateway.ha_entity_registry,
                member.device.device_id,
                include_disabled_entities=True,
            )
            all_domain_occurrences.extend(
                [
                    entity.domain
                    for entity in entities
                    if entity.domain in zha_regs.GROUP_ENTITY_DOMAINS
                ]
            )
        if not all_domain_occurrences:
            return entity_domains
        # get all domains we care about if there are more than 2 entities of this domain
        counts = Counter(all_domain_occurrences)
        entity_domains = [domain[0] for domain in counts.items() if domain[1] >= 2]
        _LOGGER.debug(
            "The entity domains are: %s for group: %s:0x%04x",
            entity_domains,
            group.name,
            group.group_id,
        )
        return entity_domains

"""
PROBE = ProbeEndpoint()
""" TODO
GROUP_PROBE = GroupProbe()
"""
