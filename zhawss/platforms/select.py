"""Select platform for zhawss."""

from enum import Enum
import functools

import zigpy.types as t
from zigpy.zcl.clusters.security import IasWd

from zhawss.platforms import PlatformEntity
from zhawss.platforms.registries import PLATFORM_ENTITIES, Platform
from zhawss.zigbee.cluster.const import CLUSTER_HANDLER_IAS_WD

MULTI_MATCH = functools.partial(PLATFORM_ENTITIES.multipass_match, Platform.SELECT)


class Strobe(t.enum8):
    """Strobe enum."""

    No_Strobe = 0x00
    Strobe = 0x01


class EnumSelect(PlatformEntity):

    PLATFORM = Platform.SELECT
    _enum: Enum = None

    def to_json(self) -> dict:
        """Return a JSON representation of the select."""
        json = super().to_json()
        json["enum"] = self._enum.name
        json["options"] = self._enum._member_names_
        return json


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
