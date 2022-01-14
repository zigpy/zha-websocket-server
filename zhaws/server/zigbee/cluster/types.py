"""Types for zhawss."""
from typing import TYPE_CHECKING, Dict

ClientClusterHandlerType = "ClientClusterHandler"
ClusterHandlerType = "ClusterHandler"
ZDOClusterHandlerType = "ZDOClusterHandler"
ClusterHandlerDictType = "ClusterHandlerDict"

if TYPE_CHECKING:
    from zhaws.server.zigbee.cluster import (
        ClientClusterHandler,
        ClusterHandler,
        ZDOClusterHandler,
    )

    ClusterHandlerType = ClusterHandler
    ZDOClusterHandlerType = ZDOClusterHandler
    ClientClusterHandlerType = ClientClusterHandler
    ClusterHandlerDictType = Dict[str, ClusterHandler]
