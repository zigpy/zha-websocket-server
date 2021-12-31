"""Typing helpers for zhawss."""
from typing import TYPE_CHECKING

ControllerType = "Controller"

if TYPE_CHECKING:
    from zhawss.application.controller import Controller

    ControllerType = Controller
