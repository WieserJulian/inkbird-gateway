"""Unit tests for IBS-M1S device connection (standalone, no Home Assistant required)."""

from __future__ import annotations

import asyncio
import json
import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Any, Dict

# Import the device config module (no HA dependency)
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from custom_components.inkbird_gateway.device_config import (
    DeviceConfig,
    IntegrationConfig,
)


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

        # Verify it's valid JSON
        data = json.loads(json_str)
        self.assertEqual(data["device_id"], "test123")
        self.assertEqual(data["local_key"], "test_key")

    def test_device_config_from_dict(self):
        """Test creating device config from dictionary."""
        data = {
            "device_id": "test123",
            "local_key": "test_key",
            "ip_address": "192.168.1.40",
            "protocol_version": "3.4",
        }

        config = DeviceConfig.from_dict(data)

        self.assertEqual(config.device_id, "test123")
        self.assertEqual(config.local_key, "test_key")
        self.assertEqual(config.protocol_version, "3.4")

    def test_device_config_from_json(self):
        """Test creating device config from JSON."""
        json_str = json.dumps(
            {
                "device_id": "test123",
                "local_key": "test_key",
                "ip_address": "192.168.1.40",
            }
        )

        config = DeviceConfig.from_json(json_str)

        self.assertEqual(config.device_id, "test123")
        self.assertEqual(config.ip_address, "192.168.1.40")

    def test_device_config_defaults(self):
        """Test default values."""
        config = DeviceConfig(device_id="test123")

        self.assertTrue(config.use_lan)
        self.assertEqual(config.protocol_version, "3.3")
        self.assertEqual(config.channels, 4)
        self.assertEqual(config.poll_interval, 60)
        self.assertTrue(config.enabled)


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

    def test_integration_config_to_dict(self):
        """Test converting integration config to dictionary."""
        config = IntegrationConfig()
        config.add_device(DeviceConfig(device_id="dev1"))

        config_dict = config.to_dict()

        self.assertEqual(len(config_dict["devices"]), 1)
        self.assertEqual(config_dict["devices"][0]["device_id"], "dev1")

    def test_integration_config_to_json(self):
        """Test converting integration config to JSON."""
        config = IntegrationConfig()
        config.add_device(DeviceConfig(device_id="dev1", name="Test Device"))

        json_str = config.to_json()
        data = json.loads(json_str)

        self.assertEqual(len(data["devices"]), 1)
        self.assertEqual(data["devices"][0]["device_id"], "dev1")

    def test_integration_config_from_dict(self):
        """Test creating integration config from dictionary."""
        data = {
            "devices": [
                {"device_id": "dev1", "local_key": "key1"},
                {"device_id": "dev2", "local_key": "key2"},
            ],
            "endpoint": "https://openapi.tuyaeu.com",
            "scan_interval": 45,
        }

        config = IntegrationConfig.from_dict(data)

        self.assertEqual(len(config.devices), 2)
        self.assertEqual(config.devices[0].device_id, "dev1")
        self.assertEqual(config.endpoint, "https://openapi.tuyaeu.com")
        self.assertEqual(config.scan_interval, 45)

    def test_integration_config_from_json(self):
        """Test creating integration config from JSON."""
        json_str = json.dumps(
            {
                "devices": [{"device_id": "dev1", "local_key": "key1"}],
                "endpoint": "https://openapi.tuyaus.com",
            }
        )

        config = IntegrationConfig.from_json(json_str)

        self.assertEqual(len(config.devices), 1)
        self.assertEqual(config.devices[0].device_id, "dev1")


class TestDeviceConnectionValidation(unittest.TestCase):
    """Tests for validating device configurations."""

    def test_lan_config_has_required_fields(self):
        """Test that LAN config has device_id and local_key."""
        # Valid LAN config
        config = DeviceConfig(
            device_id="test123",
            local_key="test_key",
            ip_address="192.168.1.40",
        )

        self.assertTrue(
            config.device_id and config.local_key,
            "LAN config must have device_id and local_key",
        )

    def test_cloud_config_has_required_fields(self):
        """Test that cloud config has device_id and access credentials."""
        # Valid cloud config
        config = DeviceConfig(
            device_id="test123",
            access_id="access_id",
            access_secret="access_secret",
            use_lan=False,
        )

        self.assertTrue(
            config.device_id and config.access_id and config.access_secret,
            "Cloud config must have device_id and access credentials",
        )

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

    def test_validate_poll_interval(self):
        """Test that poll interval is reasonable."""
        config = DeviceConfig(device_id="test", poll_interval=60)
        self.assertGreaterEqual(config.poll_interval, 10)
        self.assertLessEqual(config.poll_interval, 3600)


class TestDeviceConnectionSimulation(unittest.TestCase):
    """Simulated device connection tests (no actual network calls)."""

    def test_mock_lan_connection(self):
        """Test simulating a LAN connection."""
        # Create mock device
        device_config = DeviceConfig(
            device_id="test123",
            local_key="test_key",
            ip_address="192.168.188.40",
            protocol_version="3.3",
        )

        # Simulate connection parameters
        self.assertEqual(device_config.ip_address, "192.168.188.40")
        self.assertEqual(device_config.local_key, "test_key")
        self.assertTrue(device_config.use_lan)

    def test_mock_device_status_parsing(self):
        """Test parsing mock device status response."""
        # Simulate device response format A (individual DPs)
        mock_response = {
            "dps": {
                "1": 24.5,  # CH0 Temperature
                "2": 65,    # CH0 Humidity
                "3": 85,    # CH0 Battery
                "4": 23.2,  # CH1 Temperature
                "5": 62,    # CH1 Humidity
                "6": 92,    # CH1 Battery
                "7": 22.1,  # CH2 Temperature
                "8": 58,    # CH2 Humidity
                "9": 78,    # CH2 Battery
                "10": 21.8, # CH3 Temperature
                "11": 55,   # CH3 Humidity
                "12": 88,   # CH3 Battery
            }
        }

        # Parse format A
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

        # Verify parsing
        self.assertEqual(channels[0]["temperature"], 24.5)
        self.assertEqual(channels[0]["humidity"], 65)
        self.assertEqual(channels[0]["battery"], 85)
        self.assertEqual(len(channels), 4)

    def test_mock_device_status_format_b(self):
        """Test parsing mock device status response format B."""
        # Simulate device response format B (nested channels)
        mock_response = {
            "dps": {
                "ch_0": {"temp": 24.5, "humi": 65, "bat": 85},
                "ch_1": {"temp": 23.2, "humi": 62, "bat": 92},
                "ch_2": {"temp": 22.1, "humi": 58, "bat": 78},
                "ch_3": {"temp": 21.8, "humi": 55, "bat": 88},
            }
        }

        # Parse format B
        channels = {}
        for i in range(4):
            ch_key = f"ch_{i}"
            if ch_key in mock_response["dps"]:
                channels[i] = {
                    "temperature": mock_response["dps"][ch_key].get("temp"),
                    "humidity": mock_response["dps"][ch_key].get("humi"),
                    "battery": mock_response["dps"][ch_key].get("bat"),
                }

        # Verify parsing
        self.assertEqual(channels[0]["temperature"], 24.5)
        self.assertEqual(channels[1]["humidity"], 62)
        self.assertEqual(channels[2]["battery"], 78)
        self.assertEqual(len(channels), 4)


class TestDeviceSensorMapping(unittest.TestCase):
    """Tests for mapping device data to Home Assistant sensors."""

    def test_create_sensor_entities_from_config(self):
        """Test creating sensor entity names from device config."""
        device = DeviceConfig(
            device_id="dev1",
            name="Living Room",
            channels=4,
        )

        # Simulate sensor creation
        sensors = []
        for channel in range(device.channels):
            sensors.append(f"{device.name} CH{channel} Temperature")
            sensors.append(f"{device.name} CH{channel} Humidity")
            sensors.append(f"{device.name} CH{channel} Battery")

        self.assertEqual(len(sensors), 12)  # 4 channels × 3 sensors
        self.assertIn("Living Room CH0 Temperature", sensors)
        self.assertIn("Living Room CH3 Battery", sensors)

    def test_sensor_entity_ids(self):
        """Test generating valid Home Assistant entity IDs."""
        device_name = "Living Room Sensor"

        # Simulate entity ID generation
        entity_ids = []
        for channel in range(4):
            entity_id_base = device_name.lower().replace(" ", "_")
            entity_ids.append(f"sensor.{entity_id_base}_ch{channel}_temperature")
            entity_ids.append(f"sensor.{entity_id_base}_ch{channel}_humidity")
            entity_ids.append(f"sensor.{entity_id_base}_ch{channel}_battery")

        self.assertEqual(len(entity_ids), 12)
        self.assertIn("sensor.living_room_sensor_ch0_temperature", entity_ids)


def run_tests():
    """Run all tests."""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestDeviceConfig))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegrationConfig))
    suite.addTests(loader.loadTestsFromTestCase(TestDeviceConnectionValidation))
    suite.addTests(loader.loadTestsFromTestCase(TestDeviceConnectionSimulation))
    suite.addTests(loader.loadTestsFromTestCase(TestDeviceSensorMapping))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)
