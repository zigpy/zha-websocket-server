"""Mapping registries for zhawss."""

from typing import Final

from zhaws.server.zigbee.decorators import DictRegistry, SetRegistry

PHILLIPS_REMOTE_CLUSTER: Final[int] = 0xFC00
SMARTTHINGS_ACCELERATION_CLUSTER: Final[int] = 0xFC02
SMARTTHINGS_HUMIDITY_CLUSTER: Final[int] = 0xFC45
VOC_LEVEL_CLUSTER: Final[int] = 0x042E

BINDABLE_CLUSTERS = SetRegistry()
HANDLER_ONLY_CLUSTERS = SetRegistry()
CLIENT_CLUSTER_HANDLER_REGISTRY = DictRegistry()
CLUSTER_HANDLER_REGISTRY = DictRegistry()
