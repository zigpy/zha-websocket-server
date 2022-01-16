"""Utils for zhawss."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from zigpy.zcl import Cluster as ZigpyCluster

if TYPE_CHECKING:
    from zhaws.server.zigbee.cluster import ClusterHandler


async def safe_read(
    cluster: ZigpyCluster,
    attributes: list,
    allow_cache: bool = True,
    only_cache: bool = False,
    manufacturer: int | None = None,
) -> dict:
    """Swallow all exceptions from network read.
    If we throw during initialization, setup fails. Rather have an entity that
    exists, but is in a maybe wrong state, than no entity. This method should
    probably only be used during initialization.
    """
    try:
        result, _ = await cluster.read_attributes(
            attributes,
            allow_cache=allow_cache,
            only_cache=only_cache,
            manufacturer=manufacturer,
        )
        return result
    except Exception:  # pylint: disable=broad-except
        return {}


def parse_and_log_command(
    cluster_handler: ClusterHandler, tsn: int, command_id: int, args: Any
) -> str:
    """Parse and log a zigbee cluster command."""
    cmd: str = cluster_handler.cluster.server_commands.get(command_id, [command_id])[0]
    cluster_handler.debug(
        "received '%s' command with %s args on cluster_id '%s' tsn '%s'",
        cmd,
        args,
        cluster_handler.cluster.cluster_id,
        tsn,
    )
    return cmd
