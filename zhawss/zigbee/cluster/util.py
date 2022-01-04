"""Utils for zhawss."""


async def safe_read(
    cluster, attributes, allow_cache=True, only_cache=False, manufacturer=None
):
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


def parse_and_log_command(cluster_handler, tsn, command_id, args):
    """Parse and log a zigbee cluster command."""
    cmd = cluster_handler.cluster.server_commands.get(command_id, [command_id])[0]
    cluster_handler.debug(
        "received '%s' command with %s args on cluster_id '%s' tsn '%s'",
        cmd,
        args,
        cluster_handler.cluster.cluster_id,
        tsn,
    )
    return cmd
