"""Types for zhawss platform module."""

from typing import TYPE_CHECKING

PlatformEntityType = "PlatformEntityType"

if TYPE_CHECKING:
    from zhaws.server.platforms import PlatformEntity

    PlatformEntityType = PlatformEntity
