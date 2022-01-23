"""Select platform for zhawss."""
from __future__ import annotations

from enum import Enum
import functools
from typing import TYPE_CHECKING, Any, Final, Union

import zigpy.types as t
from zigpy.zcl.clusters.security import IasWd

from zhaws.server.platforms import PlatformEntity
from zhaws.server.platforms.registries import PLATFORM_ENTITIES, Platform
from zhaws.server.zigbee.cluster.const import CLUSTER_HANDLER_IAS_WD

if TYPE_CHECKING:
    from zhaws.server.zigbee.cluster import ClusterHandler
    from zhaws.server.zigbee.device import Device
    from zhaws.server.zigbee.endpoint import Endpoint

MULTI_MATCH = functools.partial(PLATFORM_ENTITIES.multipass_match, Platform.SELECT)
STATE_UNKNOWN: Final[str] = "unknown"


class Strobe(t.enum8):  # type: ignore #TODO fix type
    No_Strobe = 0x00
    Strobe = 0x01


class EnumSelect(PlatformEntity):

    PLATFORM = Platform.SELECT
    _enum: type[Enum]

    def __init__(
        self,
        unique_id: str,
        cluster_handlers: list[ClusterHandler],
        endpoint: Endpoint,
        device: Device,
    ):
        """Initialize the select entity."""
        self._attr_name = self._enum.__name__
        self._attr_options = [entry.name.replace("_", " ") for entry in self._enum]
        super().__init__(unique_id, cluster_handlers, endpoint, device)
        self._cluster_handler: ClusterHandler = cluster_handlers[0]

        """TODO
        self._cluster_handler.data_cache[self._attr_name] = self._enum[
                last_state.state.replace(" ", "_")
            ]
        """

    @property
    def current_option(self) -> Union[str, None]:
        """Return the selected entity option to represent the entity state."""
        option = self._cluster_handler.data_cache.get(self._attr_name)
        if option is None:
            return None
        return option.name.replace("_", " ")

    async def async_select_option(self, option: Union[str, int], **kwargs: Any) -> None:
        """Change the selected option."""
        if isinstance(option, str):
            self._cluster_handler.data_cache[self._attr_name] = self._enum[
                option.replace(" ", "_")
            ]
            self.maybe_send_state_changed_event()

    def to_json(self) -> dict:
        """Return a JSON representation of the select."""
        json = super().to_json()
        json["enum"] = self._enum.__name__
        json["options"] = self._attr_options
        return json

    def get_state(self) -> dict:
        """Return the state of the select."""
        response = super().get_state()
        response["state"] = self.current_option
        return response


@MULTI_MATCH(cluster_handler_names=CLUSTER_HANDLER_IAS_WD)
class DefaultToneSelectEntity(EnumSelect, id_suffix=IasWd.Warning.WarningMode.__name__):
    """Representation of a zhawss default siren tone select entity."""

    _enum: IasWd.Warning.WarningMode = IasWd.Warning.WarningMode


@MULTI_MATCH(cluster_handler_names=CLUSTER_HANDLER_IAS_WD)
class DefaultSirenLevelSelectEntity(
    EnumSelect, id_suffix=IasWd.Warning.SirenLevel.__name__
):
    """Representation of a zhawss default siren level select entity."""

    _enum: IasWd.Warning.SirenLevel = IasWd.Warning.SirenLevel


@MULTI_MATCH(cluster_handler_names=CLUSTER_HANDLER_IAS_WD)
class DefaultStrobeLevelSelectEntity(EnumSelect, id_suffix=IasWd.StrobeLevel.__name__):
    """Representation of a zhawss default siren strobe level select entity."""

    _enum = IasWd.StrobeLevel


@MULTI_MATCH(cluster_handler_names=CLUSTER_HANDLER_IAS_WD)
class DefaultStrobeSelectEntity(EnumSelect, id_suffix=Strobe.__name__):
    """Representation of a zhawss default siren strobe select entity."""

    _enum = Strobe
