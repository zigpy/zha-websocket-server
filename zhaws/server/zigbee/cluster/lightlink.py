"""Lightlink cluster handlers module for zhawss."""
import asyncio

import zigpy.exceptions
from zigpy.zcl.clusters import lightlink

from zhaws.server.zigbee import registries
from zhaws.server.zigbee.cluster import ClusterHandler, ClusterHandlerStatus


@registries.HANDLER_ONLY_CLUSTERS.register(lightlink.LightLink.cluster_id)
@registries.CLUSTER_HANDLER_REGISTRY.register(lightlink.LightLink.cluster_id)
class LightLink(ClusterHandler):
    """Lightlink cluster handler."""

    BIND: bool = False

    async def async_configure(self) -> None:
        """Add Coordinator to LightLink group ."""

        if self._endpoint.device.skip_configuration:
            self._status = ClusterHandlerStatus.CONFIGURED
            return

        application = self._endpoint.device.controller.application_controller
        try:
            coordinator = application.get_device(application.ieee)
        except KeyError:
            self.warning("Aborting - unable to locate required coordinator device.")
            return

        try:
            _, _, groups = await self.cluster.get_group_identifiers(0)
        except (zigpy.exceptions.ZigbeeException, asyncio.TimeoutError) as exc:
            self.warning("Couldn't get list of groups: %s", str(exc))
            return

        if groups:
            for group in groups:
                self.debug("Adding coordinator to 0x%04x group id", group.group_id)
                await coordinator.add_to_group(group.group_id)
        else:
            await coordinator.add_to_group(0x0000, name="Default Lightlink Group")
