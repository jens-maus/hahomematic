"""Tests for sensor data points of hahomematic."""

from __future__ import annotations

from typing import cast
from unittest.mock import Mock

import pytest

from hahomematic.central import CentralUnit
from hahomematic.client import Client
from hahomematic.const import DataPointUsage
from hahomematic.model.generic import DpSensor
from hahomematic.model.hub import SysvarDpSensor

from tests import const, helper

TEST_DEVICES: dict[str, str] = {
    "VCU7981740": "HmIP-SRH.json",
    "VCU3941846": "HMIP-PSM.json",
    "VCU8205532": "HmIP-SCTH230.json",
}

# pylint: disable=protected-access


@pytest.mark.asyncio
@pytest.mark.parametrize(
    (
        "address_device_translation",
        "do_mock_client",
        "add_sysvars",
        "add_programs",
        "ignore_devices_on_create",
        "un_ignore_list",
    ),
    [
        (TEST_DEVICES, True, False, False, None, None),
    ],
)
async def test_hmsensor_psm(
    central_client_factory: tuple[CentralUnit, Client | Mock, helper.Factory],
) -> None:
    """Test HmSensor."""
    central, _, _ = central_client_factory
    sensor: DpSensor = cast(DpSensor, central.get_generic_data_point("VCU3941846:6", "VOLTAGE"))
    assert sensor.usage == DataPointUsage.DATA_POINT
    assert sensor.unit == "V"
    assert sensor.values is None
    assert sensor.value is None
    await central.data_point_event(const.INTERFACE_ID, "VCU3941846:6", "VOLTAGE", 120)
    assert sensor.value == 120.0
    await central.data_point_event(const.INTERFACE_ID, "VCU3941846:6", "VOLTAGE", 234.00)
    assert sensor.value == 234.00

    sensor2: DpSensor = cast(
        DpSensor,
        central.get_generic_data_point("VCU3941846:0", "RSSI_DEVICE"),
    )
    assert sensor2.usage == DataPointUsage.DATA_POINT
    assert sensor2.unit == "dBm"
    assert sensor2.values is None
    assert sensor2.value is None
    await central.data_point_event(const.INTERFACE_ID, "VCU3941846:0", "RSSI_DEVICE", 24)
    assert sensor2.value == -24
    await central.data_point_event(const.INTERFACE_ID, "VCU3941846:0", "RSSI_DEVICE", -40)
    assert sensor2.value == -40
    await central.data_point_event(const.INTERFACE_ID, "VCU3941846:0", "RSSI_DEVICE", -160)
    assert sensor2.value == -96
    await central.data_point_event(const.INTERFACE_ID, "VCU3941846:0", "RSSI_DEVICE", 160)
    assert sensor2.value == -96
    await central.data_point_event(const.INTERFACE_ID, "VCU3941846:0", "RSSI_DEVICE", 400)
    assert sensor2.value is None

    sensor3: DpSensor = cast(
        DpSensor,
        central.get_generic_data_point("VCU8205532:1", "CONCENTRATION"),
    )
    assert sensor3.usage == DataPointUsage.DATA_POINT
    assert sensor3.unit == "ppm"
    assert sensor3.values is None
    assert sensor3.value is None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    (
        "address_device_translation",
        "do_mock_client",
        "add_sysvars",
        "add_programs",
        "ignore_devices_on_create",
        "un_ignore_list",
    ),
    [
        (TEST_DEVICES, True, False, False, None, None),
    ],
)
async def test_hmsensor_srh(
    central_client_factory: tuple[CentralUnit, Client | Mock, helper.Factory],
) -> None:
    """Test HmSensor."""
    central, _, _ = central_client_factory
    sensor: DpSensor = cast(DpSensor, central.get_generic_data_point("VCU7981740:1", "STATE"))
    assert sensor.usage == DataPointUsage.DATA_POINT
    assert sensor.unit is None
    assert sensor.values == ("CLOSED", "TILTED", "OPEN")
    assert sensor.value is None
    await central.data_point_event(const.INTERFACE_ID, "VCU7981740:1", "STATE", 0)
    assert sensor.value == "CLOSED"
    await central.data_point_event(const.INTERFACE_ID, "VCU7981740:1", "STATE", 2)
    assert sensor.value == "OPEN"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    (
        "address_device_translation",
        "do_mock_client",
        "add_sysvars",
        "add_programs",
        "ignore_devices_on_create",
        "un_ignore_list",
    ),
    [
        ({}, True, True, False, None, None),
    ],
)
async def test_hmsysvarsensor(
    central_client_factory: tuple[CentralUnit, Client | Mock, helper.Factory],
) -> None:
    """Test HmSysvarSensor."""
    central, _, _ = central_client_factory
    sensor: SysvarDpSensor = cast(SysvarDpSensor, central.get_sysvar_data_point("sv_list"))
    assert sensor.usage == DataPointUsage.DATA_POINT
    assert sensor.available is True
    assert sensor.unit is None
    assert sensor.values == ("v1", "v2", "v3")
    assert sensor.value == "v1"

    sensor2: SysvarDpSensor = cast(SysvarDpSensor, central.get_sysvar_data_point("sv_float"))
    assert sensor2.usage == DataPointUsage.DATA_POINT
    assert sensor2.unit is None
    assert sensor2.values is None
    assert sensor2.value == 23.2
