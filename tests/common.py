"""Common test objects."""
from typing import Any, Coroutine
from unittest.mock import AsyncMock, Mock

import zigpy.zcl
import zigpy.zcl.foundation as zcl_f

from zhaws.server.zigbee.device import Device


def patch_cluster(cluster: zigpy.zcl.Cluster) -> None:
    """Patch a cluster for testing."""
    cluster.PLUGGED_ATTR_READS = {}

    async def _read_attribute_raw(attributes: Any, *args: Any, **kwargs: Any) -> Any:
        result = []
        for attr_id in attributes:
            value = cluster.PLUGGED_ATTR_READS.get(attr_id)
            if value is None:
                # try converting attr_id to attr_name and lookup the plugs again
                attr_name = cluster.attributes.get(attr_id)
                value = attr_name and cluster.PLUGGED_ATTR_READS.get(attr_name[0])
            if value is not None:
                result.append(
                    zcl_f.ReadAttributeRecord(
                        attr_id,
                        zcl_f.Status.SUCCESS,
                        zcl_f.TypeValue(python_type=None, value=value),
                    )
                )
            else:
                result.append(zcl_f.ReadAttributeRecord(attr_id, zcl_f.Status.FAILURE))
        return (result,)

    cluster.bind = AsyncMock(return_value=[0])
    cluster.configure_reporting = AsyncMock(
        return_value=[
            [zcl_f.ConfigureReportingResponseRecord(zcl_f.Status.SUCCESS, 0x00, 0xAABB)]
        ]
    )
    cluster.configure_reporting_multiple = AsyncMock(
        return_value=zcl_f.ConfigureReportingResponse.deserialize(b"\x00")[0]
    )
    cluster.deserialize = Mock()
    cluster.handle_cluster_request = Mock()
    cluster.read_attributes = AsyncMock(wraps=cluster.read_attributes)
    cluster.read_attributes_raw = AsyncMock(side_effect=_read_attribute_raw)
    cluster.unbind = AsyncMock(return_value=[0])
    cluster.write_attributes = AsyncMock(wraps=cluster.write_attributes)
    cluster._write_attributes = AsyncMock(
        return_value=[zcl_f.WriteAttributesResponse.deserialize(b"\x00")[0]]
    )
    if cluster.cluster_id == 4:
        cluster.add = AsyncMock(return_value=[0])


def update_attribute_cache(cluster: zigpy.zcl.Cluster) -> None:
    """Update attribute cache based on plugged attributes."""
    if cluster.PLUGGED_ATTR_READS:
        attrs = [
            make_attribute(cluster.attridx.get(attr, attr), value)
            for attr, value in cluster.PLUGGED_ATTR_READS.items()
        ]
        hdr = make_zcl_header(zcl_f.Command.Report_Attributes)
        hdr.frame_control.disable_default_response = True
        cluster.handle_message(hdr, [attrs])


def make_attribute(attrid: int, value: Any, status: int = 0) -> zcl_f.Attribute:
    """Make an attribute."""
    attr = zcl_f.Attribute()
    attr.attrid = attrid
    attr.value = zcl_f.TypeValue()
    attr.value.value = value
    return attr


def send_attribute_report(
    cluster: zigpy.zcl.Cluster, attrid: int, value: Any
) -> Coroutine:
    """Send a single attribute report."""
    return send_attributes_report(cluster, {attrid: value})


async def send_attributes_report(cluster: zigpy.zcl.Cluster, attributes: dict) -> None:
    """Cause the sensor to receive an attribute report from the network.

    This is to simulate the normal device communication that happens when a
    device is paired to the zigbee network.
    """
    attrs = [
        make_attribute(cluster.attridx.get(attr, attr), value)
        for attr, value in attributes.items()
    ]
    hdr = make_zcl_header(zcl_f.Command.Report_Attributes)
    hdr.frame_control.disable_default_response = True
    cluster.handle_message(hdr, [attrs])
    # await hass.async_block_till_done()


async def async_enable_traffic(zha_devices: list[Device], enabled: bool = True) -> None:
    """Allow traffic to flow through the gateway and the zha device."""
    for zha_device in zha_devices:
        zha_device.update_available(enabled)
    # await hass.async_block_till_done()


def make_zcl_header(
    command_id: int, global_command: bool = True, tsn: int = 1
) -> zcl_f.ZCLHeader:
    """Cluster.handle_message() ZCL Header helper."""
    if global_command:
        frc = zcl_f.FrameControl(zcl_f.FrameType.GLOBAL_COMMAND)
    else:
        frc = zcl_f.FrameControl(zcl_f.FrameType.CLUSTER_COMMAND)
    return zcl_f.ZCLHeader(frc, tsn=tsn, command_id=command_id)


def reset_clusters(clusters: list[zigpy.zcl.Cluster]) -> None:
    """Reset mocks on cluster."""
    for cluster in clusters:
        cluster.bind.reset_mock()
        cluster.configure_reporting.reset_mock()
        cluster.configure_reporting_multiple.reset_mock()
        cluster.write_attributes.reset_mock()
