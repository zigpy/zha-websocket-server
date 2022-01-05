"""Mapping registries for zhawss."""

# importing cluster handlers updates registries
from zhawss.zigbee import (  # noqa: F401 pylint: disable=unused-import
    cluster as zha_cluster_handlers,
)
from zhawss.zigbee.decorators import DictRegistry, SetRegistry

PHILLIPS_REMOTE_CLUSTER = 0xFC00
SMARTTHINGS_ACCELERATION_CLUSTER = 0xFC02
SMARTTHINGS_HUMIDITY_CLUSTER = 0xFC45
VOC_LEVEL_CLUSTER = 0x042E

BINDABLE_CLUSTERS = SetRegistry()
HANDLER_ONLY_CLUSTERS = SetRegistry()
CLIENT_CLUSTER_HANDLER_REGISTRY = DictRegistry()
CLUSTER_HANDLER_REGISTRY = DictRegistry()
