"""Pre-configuration & device settings for Inkbird Gateway."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Optional
import json
from pathlib import Path


@dataclass
class DeviceConfig:
    """Configuration for a single Inkbird device (LAN or Tuya)."""

    device_id: str
    """The unique device ID (required)."""

    # LAN Connection (direct local protocol)
    local_key: Optional[str] = None
    """Local encryption key for Tuya LAN protocol (optional)."""

    ip_address: Optional[str] = None
    """Direct IP address for LAN connections (optional, auto-discovered if not set)."""

    protocol_version: str = "3.3"
    """Tuya protocol version: 3.3, 3.4, or 3.5 (default: 3.3)."""

    use_lan: bool = True
    """Prefer direct LAN connection over cloud (default: True)."""

    # Cloud Connection (Tuya OpenAPI)
    access_id: Optional[str] = None
    """Tuya OpenAPI Access ID (optional, for cloud fallback)."""

    access_secret: Optional[str] = None
    """Tuya OpenAPI Access Secret (optional, for cloud fallback)."""

    # Metadata
    name: Optional[str] = None
    """User-friendly device name (optional, auto-detected if not set)."""

    model: Optional[str] = None
    """Device model (optional, auto-detected if not set)."""

    channels: int = 4
    """Number of sensor channels (default: 4 for IBS-M1S)."""

    poll_interval: int = 60
    """Polling interval in seconds (default: 60)."""

    enabled: bool = True
    """Whether this device is enabled (default: True)."""

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
    """List of configured devices."""

    endpoint: str = "https://openapi.tuyaus.com"
    """Tuya OpenAPI endpoint (default: US)."""

    scan_interval: int = 60
    """Default polling interval in seconds."""

    log_level: str = "INFO"
    """Logging level: DEBUG, INFO, WARNING, ERROR."""

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

    @classmethod
    def from_file(cls, filepath: str | Path) -> IntegrationConfig:
        """Load from JSON file."""
        with open(filepath, "r") as f:
            return cls.from_json(f.read())

    def save_to_file(self, filepath: str | Path) -> None:
        """Save to JSON file."""
        with open(filepath, "w") as f:
            f.write(self.to_json())

    def add_device(self, device: DeviceConfig) -> None:
        """Add a device to configuration."""
        # Replace existing device with same ID or append
        self.devices = [d for d in self.devices if d.device_id != device.device_id]
        self.devices.append(device)

    def remove_device(self, device_id: str) -> None:
        """Remove a device from configuration."""
        self.devices = [d for d in self.devices if d.device_id != device_id]

    def get_device(self, device_id: str) -> Optional[DeviceConfig]:
        """Get device by ID."""
        for device in self.devices:
            if device.device_id == device_id:
                return device
        return None


# Example configuration file templates
EXAMPLE_CONFIG_YAML = """
# Inkbird Gateway Pre-Configuration
# Save as: inkbird_config.json in your Home Assistant config directory

{
  "devices": [
    {
      "device_id": "abc123def456ghi789jk",
      "local_key": "a1b2c3d4e5f6g7h8i9j0",
      "ip_address": "192.168.188.40",
      "protocol_version": "3.3",
      "use_lan": true,
      "name": "Living Room Temperature",
      "model": "IBS-M1S",
      "channels": 4,
      "poll_interval": 60,
      "enabled": true
    },
    {
      "device_id": "def456ghi789jk012lmn",
      "local_key": "k1l2m3n4o5p6q7r8s9t0",
      "ip_address": "192.168.188.41",
      "protocol_version": "3.3",
      "use_lan": true,
      "name": "Basement Temperature",
      "model": "IBS-M1S",
      "channels": 4,
      "poll_interval": 60,
      "enabled": true
    }
  ],
  "endpoint": "https://openapi.tuyaus.com",
  "scan_interval": 60,
  "log_level": "INFO"
}
"""


def create_example_config() -> IntegrationConfig:
    """Create an example configuration for reference."""
    config = IntegrationConfig()

    # Add example device
    device = DeviceConfig(
        device_id="abc123def456ghi789jk",
        local_key="a1b2c3d4e5f6g7h8i9j0",
        ip_address="192.168.188.40",
        protocol_version="3.3",
        use_lan=True,
        name="Living Room Sensor",
        model="IBS-M1S",
        channels=4,
        poll_interval=60,
        enabled=True,
    )
    config.add_device(device)

    return config
