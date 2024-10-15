"""Controller for zha web socket server."""

from __future__ import annotations

from collections.abc import Callable
import dataclasses
from enum import StrEnum
import logging
from typing import TYPE_CHECKING

from zha.application.gateway import (
    DeviceFullInitEvent,
    DeviceJoinedEvent,
    DeviceLeftEvent,
    DeviceRemovedEvent,
    Gateway,
    GroupEvent,
    RawDeviceInitializedEvent,
)
from zha.application.helpers import ZHAData
from zha.application.platforms import EntityStateChangedEvent
from zha.event import EventBase
from zha.zigbee.group import GroupInfo
from zhaws.client.model.types import Device as DeviceModel
from zhaws.server.const import (
    DEVICE,
    EVENT,
    EVENT_TYPE,
    IEEE,
    MESSAGE_TYPE,
    NWK,
    PAIRING_STATUS,
    ControllerEvents,
    EventTypes,
    MessageTypes,
    PlatformEntityEvents,
)

if TYPE_CHECKING:
    from zhaws.server.websocket.server import Server

_LOGGER = logging.getLogger(__name__)


class DevicePairingStatus(StrEnum):
    """Status of a device."""

    PAIRED = "paired"
    INTERVIEW_COMPLETE = "interview_complete"
    CONFIGURED = "configured"
    INITIALIZED = "initialized"


class Controller(EventBase):
    """Controller for the Zigbee application."""

    def __init__(self, server: Server):
        """Initialize the controller."""
        super().__init__()
        self._server: Server = server
        self.zha_gateway: Gateway | None = None
        self._unsubs: list[Callable[[], None]] = []

    @property
    def is_running(self) -> bool:
        """Return true if the controller is running."""
        return self.zha_gateway is not None

    @property
    def server(self) -> Server:
        """Return the server."""
        return self._server

    @property
    def gateway(self) -> Gateway:
        """Return the Gateway."""
        return self.zha_gateway

    async def start_network(self) -> None:
        """Start the Zigbee network."""
        if self.is_running:
            _LOGGER.warning("Attempted to start an already running Zigbee network")
            return
        _LOGGER.info("Starting Zigbee network")
        self.zha_gateway = await Gateway.async_from_config(
            ZHAData(
                config=self.server.config.zha_config,
                zigpy_config=self.server.config.zigpy_config,
            )
        )
        await self.zha_gateway.async_initialize()
        self._unsubs.append(self.zha_gateway.on_all_events(self._handle_event_protocol))
        await self.zha_gateway.async_initialize_devices_and_entities()
        for device in self.zha_gateway.devices.values():
            for entity in device.platform_entities.values():
                entity.on_all_events(self._handle_event_protocol)
        for group in self.zha_gateway.groups.values():
            for entity in group.group_entities.values():
                entity.on_all_events(self._handle_event_protocol)

    async def stop_network(self) -> None:
        """Stop the Zigbee network."""
        if self.zha_gateway is None:
            return
        for unsub in self._unsubs:
            unsub()
        await self.zha_gateway.shutdown()
        self.zha_gateway = None

    def handle_device_joined(self, event: DeviceJoinedEvent) -> None:
        """Handle device joined.

        At this point, no information about the device is known other than its
        address
        """
        _LOGGER.info(
            "Device %s - %s joined",
            event.device_info.ieee,
            f"0x{event.device_info.nwk:04x}",
        )
        self.server.client_manager.broadcast(
            {
                MESSAGE_TYPE: MessageTypes.EVENT,
                EVENT_TYPE: EventTypes.CONTROLLER_EVENT,
                EVENT: ControllerEvents.DEVICE_JOINED,
                IEEE: str(event.device_info.ieee),
                NWK: f"0x{event.device_info.nwk:04x}",
                PAIRING_STATUS: event.device_info.pairing_status,
            }
        )

    def handle_raw_device_initialized(self, event: RawDeviceInitializedEvent) -> None:
        """Handle a device initialization without quirks loaded."""
        self.server.client_manager.broadcast(
            {
                MESSAGE_TYPE: MessageTypes.EVENT,
                EVENT_TYPE: EventTypes.CONTROLLER_EVENT,
                EVENT: ControllerEvents.RAW_DEVICE_INITIALIZED,
                PAIRING_STATUS: DevicePairingStatus.INTERVIEW_COMPLETE,
                "model": event.model,
                "manufacturer": event.manufacturer,
                "signature": event.signature,
            }
        )

    def handle_device_fully_initialized(self, event: DeviceFullInitEvent) -> None:
        """Handle device joined and basic information discovered."""
        _LOGGER.info(
            "Device %s - %s initialized",
            event.device_info.ieee,
            f"0x{event.device_info.nwk:04x}",
        )

        self.server.client_manager.broadcast(
            {
                DEVICE: DeviceModel.model_validate(
                    dataclasses.asdict(event.device_info)
                ).dict(),
                "new_join": event.new_join,
                PAIRING_STATUS: DevicePairingStatus.INITIALIZED,
                MESSAGE_TYPE: MessageTypes.EVENT,
                EVENT_TYPE: EventTypes.CONTROLLER_EVENT,
                EVENT: ControllerEvents.DEVICE_FULLY_INITIALIZED,
            }
        )

        for entity in self.gateway.devices[
            event.device_info.ieee
        ].platform_entities.values():
            entity.on_all_events(self._handle_event_protocol)

    def handle_device_left(self, event: DeviceLeftEvent) -> None:
        """Handle device leaving the network."""
        _LOGGER.info("Device %s - %s left", event.ieee, f"0x{event.nwk:04x}")
        self.server.client_manager.broadcast(
            {
                MESSAGE_TYPE: MessageTypes.EVENT,
                EVENT_TYPE: EventTypes.CONTROLLER_EVENT,
                EVENT: ControllerEvents.DEVICE_LEFT,
                IEEE: str(event.ieee),
                NWK: f"0x{event.nwk:04x}",
            }
        )

    def handle_device_removed(self, event: DeviceRemovedEvent) -> None:
        """Handle device being removed from the network."""
        _LOGGER.info(
            "Removing device %s - %s",
            event.device_info.ieee,
            f"0x{event.device_info.nwk:04x}",
        )
        self.server.client_manager.broadcast(
            {
                DEVICE: DeviceModel.model_validate(
                    dataclasses.asdict(event.device_info)
                ).dict(),
                MESSAGE_TYPE: MessageTypes.EVENT,
                EVENT_TYPE: EventTypes.CONTROLLER_EVENT,
                EVENT: ControllerEvents.DEVICE_REMOVED,
            }
        )

    def handle_group_member_removed(self, event: GroupEvent) -> None:
        """Handle zigpy group member removed event."""
        self._broadcast_group_event(
            event.group_info, ControllerEvents.GROUP_MEMBER_REMOVED
        )

    def handle_group_member_added(self, event: GroupEvent) -> None:
        """Handle zigpy group member added event."""
        self._broadcast_group_event(
            event.group_info, ControllerEvents.GROUP_MEMBER_ADDED
        )

    def handle_group_added(self, event: GroupEvent) -> None:
        """Handle zigpy group added event."""
        self._broadcast_group_event(event.group_info, ControllerEvents.GROUP_ADDED)

    def handle_group_removed(self, event: GroupEvent) -> None:
        """Handle zigpy group removed event."""
        self._broadcast_group_event(event.group_info, ControllerEvents.GROUP_REMOVED)

    def _broadcast_group_event(self, group: GroupInfo, event: str) -> None:
        """Broadcast group event."""
        self.server.client_manager.broadcast(
            {
                "group": group.to_json(),
                MESSAGE_TYPE: MessageTypes.EVENT,
                EVENT_TYPE: EventTypes.CONTROLLER_EVENT,
                EVENT: event,
            }
        )

    def handle_state_changed(self, event: EntityStateChangedEvent) -> None:
        """Handle platform entity state changed event."""

        state = (
            self.gateway.devices[event.device_ieee]
            .platform_entities[(event.platform, event.unique_id)]
            .state
        )
        self.server.client_manager.broadcast(
            {
                "state": state,
                "platform_entity": {
                    "unique_id": event.unique_id,
                    "platform": event.platform,
                },
                "endpoint": {
                    "id": event.endpoint_id,
                    "unique_id": str(event.endpoint_id),
                },
                "device": {"ieee": str(event.device_ieee)},
                MESSAGE_TYPE: MessageTypes.EVENT,
                EVENT: PlatformEntityEvents.PLATFORM_ENTITY_STATE_CHANGED,
                EVENT_TYPE: EventTypes.PLATFORM_ENTITY_EVENT,
            }
        )
