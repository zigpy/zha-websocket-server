"""Zigbee radio utilities."""

import enum
from typing import Callable, Final

import bellows.zigbee.application
from zigpy.config import CONF_DEVICE_PATH  # noqa: F401 # pylint: disable=unused-import
import zigpy_deconz.zigbee.application
import zigpy_xbee.zigbee.application
import zigpy_zigate.zigbee.application
import zigpy_znp.zigbee.application

BAUD_RATES: Final[list[int]] = [
    2400,
    4800,
    9600,
    14400,
    19200,
    38400,
    57600,
    115200,
    128000,
    256000,
]


class RadioType(enum.Enum):
    """Possible options for radio type."""

    znp = (
        "ZNP = Texas Instruments Z-Stack ZNP protocol: CC253x, CC26x2, CC13x2",
        zigpy_znp.zigbee.application.ControllerApplication,
    )
    ezsp = (
        "EZSP = Silicon Labs EmberZNet protocol: Elelabs, HUSBZB-1, Telegesis",
        bellows.zigbee.application.ControllerApplication,
    )
    deconz = (
        "deCONZ = dresden elektronik deCONZ protocol: ConBee I/II, RaspBee I/II",
        zigpy_deconz.zigbee.application.ControllerApplication,
    )
    zigate = (
        "ZiGate = ZiGate Zigbee radios: PiZiGate, ZiGate USB-TTL, ZiGate WiFi",
        zigpy_zigate.zigbee.application.ControllerApplication,
    )
    xbee = (
        "XBee = Digi XBee Zigbee radios: Digi XBee Series 2, 2C, 3",
        zigpy_xbee.zigbee.application.ControllerApplication,
    )

    @classmethod
    def list(cls) -> list[str]:
        """Return a list of descriptions."""
        return [e.description for e in RadioType]

    @classmethod
    def get_by_description(cls, description: str) -> str:
        """Get radio by description."""
        for radio in cls:
            if radio.description == description:
                return radio.name
        raise ValueError

    def __init__(self, description: str, controller_cls: Callable) -> None:
        """Init instance."""
        self._desc = description
        self._ctrl_cls = controller_cls

    @property
    def controller(self) -> Callable:
        """Return controller class."""
        return self._ctrl_cls

    @property
    def description(self) -> str:
        """Return radio type description."""
        return self._desc
