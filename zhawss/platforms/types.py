"""Types for zhawss platform module."""

from typing import TYPE_CHECKING

PlatformEntityType = "PlatformEntityType"

if TYPE_CHECKING:
    from zhawss.platforms import PlatformEntity

    PlatformEntityType = PlatformEntity
