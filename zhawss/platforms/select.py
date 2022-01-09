"""Select platform for zhawss."""

from enum import Enum
import functools
from typing import Dict, Final, List, Union

import zigpy.types as t
from zigpy.zcl.clusters.security import IasWd

from zhawss.platforms import PlatformEntity
from zhawss.platforms.registries import PLATFORM_ENTITIES, Platform
from zhawss.zigbee.cluster.const import CLUSTER_HANDLER_IAS_WD
from zhawss.zigbee.cluster.types import ClusterHandlerType
from zhawss.zigbee.types import DeviceType, EndpointType

MULTI_MATCH = functools.partial(PLATFORM_ENTITIES.multipass_match, Platform.SELECT)
STATE_UNKNOWN: Final = "unknown"


class Strobe(t.enum8):
    """Strobe enum."""

    No_Strobe = 0x00
    Strobe = 0x01


class EnumSelect(PlatformEntity):

    PLATFORM = Platform.SELECT
    _enum: Enum = None

    def __init__(
        self,
        unique_id: str,
        cluster_handlers: List[ClusterHandlerType],
        endpoint: EndpointType,
        device: DeviceType,
    ):
        """Initialize the select entity."""
        self._attr_name = self._enum.__name__
        self._attr_options = [entry.name.replace("_", " ") for entry in self._enum]
        super().__init__(unique_id, cluster_handlers, endpoint, device)
        self._cluster_handler: ClusterHandlerType = cluster_handlers[0]

        """TODO
        self._cluster_handler.data_cache[self._attr_name] = self._enum[
                last_state.state.replace(" ", "_")
            ]
        """
        self._cluster_handler.add_listener(self)

    @property
    def current_option(self) -> Union[str, None]:
        """Return the selected entity option to represent the entity state."""
        option = self._cluster_handler.data_cache.get(self._attr_name)
        if option is None:
            return None
        return option.name.replace("_", " ")

    async def async_select_option(self, option: Union[str, int]) -> None:
        """Change the selected option."""
        self._cluster_handler.data_cache[self._attr_name] = self._enum[
            option.replace(" ", "_")
        ]
        self.send_state_changed_event()

    def to_json(self) -> dict:
        """Return a JSON representation of the select."""
        json = super().to_json()
        json["enum"] = self._enum.__name__
        json["options"] = self._attr_options
        return json

    def get_state(self) -> Union[str, Dict, None]:
        return self.current_option


@MULTI_MATCH(cluster_handler_names=CLUSTER_HANDLER_IAS_WD)
class DefaultToneSelectEntity(EnumSelect, id_suffix=IasWd.Warning.WarningMode.__name__):
    """Representation of a zhawss default siren tone select entity."""

    _enum: Enum = IasWd.Warning.WarningMode


@MULTI_MATCH(cluster_handler_names=CLUSTER_HANDLER_IAS_WD)
class DefaultSirenLevelSelectEntity(
    EnumSelect, id_suffix=IasWd.Warning.SirenLevel.__name__
):
    """Representation of a zhawss default siren level select entity."""

    _enum: Enum = IasWd.Warning.SirenLevel


@MULTI_MATCH(cluster_handler_names=CLUSTER_HANDLER_IAS_WD)
class DefaultStrobeLevelSelectEntity(EnumSelect, id_suffix=IasWd.StrobeLevel.__name__):
    """Representation of a zhawss default siren strobe level select entity."""

    _enum: Enum = IasWd.StrobeLevel


@MULTI_MATCH(cluster_handler_names=CLUSTER_HANDLER_IAS_WD)
class DefaultStrobeSelectEntity(EnumSelect, id_suffix=Strobe.__name__):
    """Representation of a zhawss default siren strobe select entity."""

    _enum: Enum = Strobe
