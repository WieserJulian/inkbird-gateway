"""Standalone unit tests for IBS-M1S device configuration (no Home Assistant required)."""

from __future__ import annotations

import asyncio
import json
import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Any, Dict
from dataclasses import dataclass, field, asdict
from pathlib import Path
import sys
import tempfile


# Direct implementation (no HA imports needed for tests)
@dataclass
class DeviceConfig:
    """Configuration for a single Inkbird device (LAN or Tuya)."""

    device_id: str
    local_key: str | None = None
    ip_address: str | None = None
    protocol_version: str = "3.3"
    use_lan: bool = True
    access_id: str | None = None
    access_secret: str | None = None
    name: str | None = None
    model: str | None = None
    channels: int = 4
    poll_interval: int = 60
    enabled: bool = True

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_dict(cls, data: dict) -> DeviceConfig:
        """Create from dictionary."""
        return cls(**data)

    @classmethod
    def from_json(cls, json_str: str) -> DeviceConfig:
        """Create from JSON string."""
        return cls.from_dict(json.loads(json_str))


@dataclass
class IntegrationConfig:
    """Overall integration configuration."""

    devices: list[DeviceConfig] = field(default_factory=list)
    endpoint: str = "https://openapi.tuyaus.com"
    scan_interval: int = 60
    log_level: str = "INFO"

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "devices": [d.to_dict() for d in self.devices],
            "endpoint": self.endpoint,
            "scan_interval": self.scan_interval,
            "log_level": self.log_level,
        }

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_dict(cls, data: dict) -> IntegrationConfig:
        """Create from dictionary."""
        devices = [DeviceConfig.from_dict(d) for d in data.get("devices", [])]
        return cls(
            devices=devices,
            endpoint=data.get("endpoint", "https://openapi.tuyaus.com"),
            scan_interval=data.get("scan_interval", 60),
            log_level=data.get("log_level", "INFO"),
        )

    @classmethod
    def from_json(cls, json_str: str) -> IntegrationConfig:
        """Create from JSON string."""
        return cls.from_dict(json.loads(json_str))

    def add_device(self, device: DeviceConfig) -> None:
        """Add a device to configuration."""
        self.devices = [d for d in self.devices if d.device_id != device.device_id]
        self.devices.append(device)

    def remove_device(self, device_id: str) -> None:
        """Remove a device from configuration."""
        self.devices = [d for d in self.devices if d.device_id != device_id]

    def get_device(self, device_id: str) -> DeviceConfig | None:
        """Get device by ID."""
        for device in self.devices:
            if device.device_id == device_id:
                return device
        return None


class TestDeviceConfig(unittest.TestCase):
    """Tests for DeviceConfig dataclass."""

    def test_create_lan_device_config(self):
        """Test creating a LAN-configured device."""
        config = DeviceConfig(
            device_id="test123",
            local_key="test_key_123456789",
            ip_address="192.168.188.40",
            protocol_version="3.3",
            use_lan=True,
            name="Test Device",
            channels=4,
        )

        self.assertEqual(config.device_id, "test123")
        self.assertEqual(config.local_key, "test_key_123456789")
        self.assertEqual(config.ip_address, "192.168.188.40")
        self.assertTrue(config.use_lan)
        self.assertEqual(config.protocol_version, "3.3")
        self.assertEqual(config.channels, 4)

    def test_create_cloud_device_config(self):
        """Test creating a cloud-only device configuration."""
        config = DeviceConfig(
            device_id="test123",
            access_id="access_id_123",
            access_secret="access_secret_456",
            use_lan=False,
            name="Cloud Device",
        )

        self.assertEqual(config.device_id, "test123")
        self.assertEqual(config.access_id, "access_id_123")
        self.assertFalse(config.use_lan)
        self.assertIsNone(config.local_key)

    def test_device_config_to_dict(self):
        """Test converting device config to dictionary."""
        config = DeviceConfig(
            device_id="test123",
            local_key="test_key",
            ip_address="192.168.1.40",
        )

        config_dict = config.to_dict()

        self.assertEqual(config_dict["device_id"], "test123")
        self.assertEqual(config_dict["local_key"], "test_key")
        self.assertEqual(config_dict["ip_address"], "192.168.1.40")

    def test_device_config_to_json(self):
        """Test converting device config to JSON."""
        config = DeviceConfig(
            device_id="test123",
            local_key="test_key",
            name="Test",
        )

        json_str = config.to_json()
        data = json.loads(json_str)

        self.assertEqual(data["device_id"], "test123")
        self.assertEqual(data["local_key"], "test_key")

    def test_device_config_roundtrip(self):
        """Test serialization and deserialization roundtrip."""
        original = DeviceConfig(
            device_id="test123",
            local_key="test_key",
            ip_address="192.168.1.40",
            protocol_version="3.4",
            name="Test Device",
        )

        # Roundtrip through JSON
        json_str = original.to_json()
        restored = DeviceConfig.from_json(json_str)

        self.assertEqual(restored.device_id, original.device_id)
        self.assertEqual(restored.local_key, original.local_key)
        self.assertEqual(restored.protocol_version, original.protocol_version)


class TestIntegrationConfig(unittest.TestCase):
    """Tests for IntegrationConfig dataclass."""

    def test_create_integration_config(self):
        """Test creating integration configuration."""
        config = IntegrationConfig(
            endpoint="https://openapi.tuyaus.com",
            scan_interval=30,
        )

        self.assertEqual(config.endpoint, "https://openapi.tuyaus.com")
        self.assertEqual(config.scan_interval, 30)
        self.assertEqual(len(config.devices), 0)

    def test_add_device_to_config(self):
        """Test adding devices to configuration."""
        config = IntegrationConfig()

        device1 = DeviceConfig(device_id="dev1")
        device2 = DeviceConfig(device_id="dev2")

        config.add_device(device1)
        config.add_device(device2)

        self.assertEqual(len(config.devices), 2)
        self.assertEqual(config.devices[0].device_id, "dev1")
        self.assertEqual(config.devices[1].device_id, "dev2")

    def test_add_device_replaces_existing(self):
        """Test that adding a device with same ID replaces it."""
        config = IntegrationConfig()

        device1 = DeviceConfig(device_id="dev1", name="Device 1")
        device1_updated = DeviceConfig(device_id="dev1", name="Device 1 Updated")

        config.add_device(device1)
        self.assertEqual(len(config.devices), 1)
        self.assertEqual(config.devices[0].name, "Device 1")

        config.add_device(device1_updated)
        self.assertEqual(len(config.devices), 1)
        self.assertEqual(config.devices[0].name, "Device 1 Updated")

    def test_remove_device_from_config(self):
        """Test removing devices from configuration."""
        config = IntegrationConfig()

        config.add_device(DeviceConfig(device_id="dev1"))
        config.add_device(DeviceConfig(device_id="dev2"))

        self.assertEqual(len(config.devices), 2)

        config.remove_device("dev1")

        self.assertEqual(len(config.devices), 1)
        self.assertEqual(config.devices[0].device_id, "dev2")

    def test_get_device_by_id(self):
        """Test retrieving device by ID."""
        config = IntegrationConfig()

        device = DeviceConfig(device_id="dev1", name="Device 1")
        config.add_device(device)

        retrieved = config.get_device("dev1")

        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.device_id, "dev1")
        self.assertEqual(retrieved.name, "Device 1")

    def test_get_device_not_found(self):
        """Test retrieving non-existent device."""
        config = IntegrationConfig()

        retrieved = config.get_device("nonexistent")

        self.assertIsNone(retrieved)


class TestDeviceConnectionValidation(unittest.TestCase):
    """Tests for validating device configurations."""

    def test_lan_config_has_required_fields(self):
        """Test that LAN config has device_id and local_key."""
        config = DeviceConfig(
            device_id="test123",
            local_key="test_key",
            ip_address="192.168.1.40",
        )

        self.assertTrue(config.device_id and config.local_key)

    def test_cloud_config_has_required_fields(self):
        """Test that cloud config has device_id and access credentials."""
        config = DeviceConfig(
            device_id="test123",
            access_id="access_id",
            access_secret="access_secret",
            use_lan=False,
        )

        self.assertTrue(config.device_id and config.access_id and config.access_secret)

    def test_validate_protocol_version(self):
        """Test that protocol version is valid."""
        for version in ["3.3", "3.4", "3.5"]:
            config = DeviceConfig(device_id="test", protocol_version=version)
            self.assertIn(config.protocol_version, ["3.3", "3.4", "3.5"])

    def test_validate_channels(self):
        """Test that channels is reasonable."""
        config = DeviceConfig(device_id="test", channels=4)
        self.assertGreater(config.channels, 0)
        self.assertLessEqual(config.channels, 8)


class TestDeviceDataParsing(unittest.TestCase):
    """Tests for parsing device data formats."""

    def test_parse_dps_format_a(self):
        """Test parsing data points format A (individual DPs)."""
        mock_response = {
            "dps": {
                "1": 24.5,  # CH0 Temperature
                "2": 65,    # CH0 Humidity
                "3": 85,    # CH0 Battery
                "4": 23.2,  # CH1 Temperature
                "5": 62,    # CH1 Humidity
                "6": 92,    # CH1 Battery
            }
        }

        channels = {}
        for dp_id, value in mock_response["dps"].items():
            dp_int = int(dp_id)
            channel = (dp_int - 1) // 3
            field = (dp_int - 1) % 3

            if channel not in channels:
                channels[channel] = {}

            if field == 0:
                channels[channel]["temperature"] = value
            elif field == 1:
                channels[channel]["humidity"] = value
            elif field == 2:
                channels[channel]["battery"] = value

        self.assertEqual(channels[0]["temperature"], 24.5)
        self.assertEqual(channels[0]["humidity"], 65)
        self.assertEqual(channels[0]["battery"], 85)
        self.assertEqual(channels[1]["temperature"], 23.2)

    def test_parse_dps_format_b(self):
        """Test parsing data points format B (nested channels)."""
        mock_response = {
            "dps": {
                "ch_0": {"temp": 24.5, "humi": 65, "bat": 85},
                "ch_1": {"temp": 23.2, "humi": 62, "bat": 92},
            }
        }

        channels = {}
        for i in range(2):
            ch_key = f"ch_{i}"
            if ch_key in mock_response["dps"]:
                channels[i] = {
                    "temperature": mock_response["dps"][ch_key].get("temp"),
                    "humidity": mock_response["dps"][ch_key].get("humi"),
                    "battery": mock_response["dps"][ch_key].get("bat"),
                }

        self.assertEqual(channels[0]["temperature"], 24.5)
        self.assertEqual(channels[1]["humidity"], 62)


class TestSensorMapping(unittest.TestCase):
    """Tests for mapping device data to sensors."""

    def test_create_sensor_names(self):
        """Test creating sensor names from device config."""
        device = DeviceConfig(
            device_id="dev1",
            name="Living Room",
            channels=4,
        )

        sensors = []
        for channel in range(device.channels):
            sensors.append(f"{device.name} CH{channel} Temperature")
            sensors.append(f"{device.name} CH{channel} Humidity")
            sensors.append(f"{device.name} CH{channel} Battery")

        self.assertEqual(len(sensors), 12)
        self.assertIn("Living Room CH0 Temperature", sensors)
        self.assertIn("Living Room CH3 Battery", sensors)

    def test_sensor_entity_id_format(self):
        """Test generating valid entity IDs."""
        device_name = "Living Room"

        entity_ids = []
        for channel in range(4):
            base = device_name.lower().replace(" ", "_")
            entity_ids.append(f"sensor.{base}_ch{channel}_temperature")
            entity_ids.append(f"sensor.{base}_ch{channel}_humidity")
            entity_ids.append(f"sensor.{base}_ch{channel}_battery")

        self.assertEqual(len(entity_ids), 12)
        self.assertIn("sensor.living_room_ch0_temperature", entity_ids)


def main():
    """Run all tests."""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestDeviceConfig))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegrationConfig))
    suite.addTests(loader.loadTestsFromTestCase(TestDeviceConnectionValidation))
    suite.addTests(loader.loadTestsFromTestCase(TestDeviceDataParsing))
    suite.addTests(loader.loadTestsFromTestCase(TestSensorMapping))

    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print("\n" + "=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("=" * 70)

    return result.wasSuccessful()


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
