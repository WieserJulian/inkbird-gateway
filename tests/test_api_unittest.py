"""Unit tests for Inkbird Gateway API parsing logic."""

from __future__ import annotations

import base64
import json
import struct
import sys
import types
import unittest
from unittest.mock import AsyncMock


def _install_test_stubs() -> None:
    """Install minimal module stubs when dependencies are unavailable."""
    if "homeassistant" not in sys.modules:
        sys.modules["homeassistant"] = types.ModuleType("homeassistant")
    if "homeassistant.helpers" not in sys.modules:
        sys.modules["homeassistant.helpers"] = types.ModuleType("homeassistant.helpers")

    if "homeassistant.const" not in sys.modules:
        homeassistant = sys.modules["homeassistant"]
        ha_const = types.ModuleType("homeassistant.const")

        class _Platform:
            SENSOR = "sensor"

        ha_const.Platform = _Platform
        homeassistant.const = ha_const
        sys.modules["homeassistant.const"] = ha_const

    if "homeassistant.config_entries" not in sys.modules:
        ha_cfg = types.ModuleType("homeassistant.config_entries")

        class _ConfigEntry:
            def __class_getitem__(cls, _item):
                return cls

        ha_cfg.ConfigEntry = _ConfigEntry
        sys.modules["homeassistant.config_entries"] = ha_cfg

    if "homeassistant.core" not in sys.modules:
        ha_core = types.ModuleType("homeassistant.core")

        class _HomeAssistant:
            pass

        ha_core.HomeAssistant = _HomeAssistant
        sys.modules["homeassistant.core"] = ha_core

    if "homeassistant.helpers.aiohttp_client" not in sys.modules:
        ha_aiohttp = types.ModuleType("homeassistant.helpers.aiohttp_client")

        def _async_get_clientsession(_hass):
            return None

        ha_aiohttp.async_get_clientsession = _async_get_clientsession
        sys.modules["homeassistant.helpers.aiohttp_client"] = ha_aiohttp

    if "homeassistant.helpers.update_coordinator" not in sys.modules:
        ha_coord = types.ModuleType("homeassistant.helpers.update_coordinator")

        class _DataUpdateCoordinator:
            def __class_getitem__(cls, _item):
                return cls

            def __init__(self, *args, **kwargs):
                pass

            async def async_config_entry_first_refresh(self):
                return None

        class _UpdateFailed(Exception):
            pass

        ha_coord.DataUpdateCoordinator = _DataUpdateCoordinator
        ha_coord.UpdateFailed = _UpdateFailed
        sys.modules["homeassistant.helpers.update_coordinator"] = ha_coord

    try:
        __import__("aiohttp")
    except ModuleNotFoundError:
        aiohttp = types.ModuleType("aiohttp")

        class _ClientError(Exception):
            pass

        class _ClientSession:
            pass

        aiohttp.ClientError = _ClientError
        aiohttp.ClientSession = _ClientSession
        sys.modules["aiohttp"] = aiohttp


_install_test_stubs()

from custom_components.inkbird_gateway.api import (  # noqa: E402
    InkbirdGatewayApi,
    InkbirdGatewayApiAuthError,
)


def _encode_channel(temp_c: float, humidity: float, battery: int, pad: int = 0) -> str:
    """Encode synthetic channel payload matching parser format."""
    payload = b"\x00" + struct.pack(
        "<hHIb",
        int(round(temp_c * 10)),
        int(round(humidity * 10)),
        pad,
        battery,
    )
    return base64.b64encode(payload).decode()


class TestInkbirdGatewayApiParser(unittest.TestCase):
    """Test parser behavior for device payloads and channels."""

    def setUp(self) -> None:
        self.api = InkbirdGatewayApi(
            session=None,  # type: ignore[arg-type]
            access_id="id",
            access_secret="secret",
            endpoint="https://openapi.tuyaus.com",
        )

    def test_decode_channel_success(self) -> None:
        raw = _encode_channel(21.5, 64.3, 78)
        parsed = self.api._decode_channel(raw)
        assert parsed is not None
        self.assertEqual(parsed.temperature, 21.5)
        self.assertEqual(parsed.humidity, 64.3)
        self.assertEqual(parsed.battery, 78)

    def test_decode_channel_filters_invalid_ranges(self) -> None:
        raw = _encode_channel(19.0, 120.0, 120)
        parsed = self.api._decode_channel(raw)
        assert parsed is not None
        self.assertEqual(parsed.temperature, 19.0)
        self.assertIsNone(parsed.humidity)
        self.assertIsNone(parsed.battery)

    def test_parse_payload_builds_channels_and_fallback(self) -> None:
        payload = {
            "name": "Pool Sensor Hub",
            "product_name": "IBS-M2",
            "pv": "1.2.3",
            "online": True,
            "status": [
                {"code": "ch_1", "value": _encode_channel(24.6, 53.2, 91)},
                {"code": "va_temperature", "value": 235},
                {"code": "va_humidity", "value": 483},
                {"code": "battery_percentage", "value": 87},
            ],
            "status_range": [
                {"code": "va_temperature", "values": json.dumps({"scale": 1})},
                {"code": "va_humidity", "values": json.dumps({"scale": 1})},
            ],
        }
        parsed = self.api._parse_device_payload("dev-1", payload)
        self.assertEqual(parsed.device_id, "dev-1")
        self.assertEqual(parsed.name, "Pool Sensor Hub")
        self.assertEqual(parsed.model, "IBS-M2")
        self.assertEqual(parsed.sw_version, "1.2.3")
        self.assertTrue(parsed.online)
        self.assertIn(1, parsed.channels)
        self.assertEqual(parsed.channels[1].temperature, 24.6)
        self.assertEqual(parsed.channels[1].humidity, 53.2)
        self.assertEqual(parsed.channels[1].battery, 91)
        self.assertIn(0, parsed.channels)
        self.assertEqual(parsed.channels[0].temperature, 23.5)
        self.assertEqual(parsed.channels[0].humidity, 48.3)
        self.assertEqual(parsed.channels[0].battery, 87)

    def test_is_supported_device(self) -> None:
        by_model = {"name": "My IBS-M1", "category": "other"}
        by_category = {"name": "Unknown", "category": "wsdcg"}
        unsupported = {"name": "Other Device", "category": "abc"}
        self.assertTrue(self.api._is_supported_device(by_model))
        self.assertTrue(self.api._is_supported_device(by_category))
        self.assertFalse(self.api._is_supported_device(unsupported))


class TestInkbirdGatewayApiAsync(unittest.IsolatedAsyncioTestCase):
    """Test async methods independent from network I/O."""

    async def test_async_get_supported_devices_filters_output(self) -> None:
        api = InkbirdGatewayApi(
            session=None,  # type: ignore[arg-type]
            access_id="id",
            access_secret="secret",
            endpoint="https://openapi.tuyaus.com",
        )
        api._uid = "user-1"
        api._async_ensure_token = AsyncMock()  # type: ignore[method-assign]
        api._async_request = AsyncMock(  # type: ignore[method-assign]
            return_value={
                "result": [
                    {"id": "a1", "name": "IBS-M2 Garden", "product_name": "IBS-M2"},
                    {"id": "a2", "name": "Other", "category": "wsdcg"},
                    {"id": "a3", "name": "Unsupported", "category": "abc"},
                ]
            }
        )
        devices = await api.async_get_supported_devices()
        self.assertEqual(len(devices), 2)
        self.assertEqual(devices[0]["id"], "a1")
        self.assertEqual(devices[1]["id"], "a2")

    async def test_async_get_supported_devices_requires_uid(self) -> None:
        api = InkbirdGatewayApi(
            session=None,  # type: ignore[arg-type]
            access_id="id",
            access_secret="secret",
            endpoint="https://openapi.tuyaus.com",
        )
        api._uid = None
        api._async_ensure_token = AsyncMock()  # type: ignore[method-assign]
        with self.assertRaises(InkbirdGatewayApiAuthError):
            await api.async_get_supported_devices()


if __name__ == "__main__":
    unittest.main()
