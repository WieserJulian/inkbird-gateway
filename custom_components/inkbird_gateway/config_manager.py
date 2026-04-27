"""Configuration file management for Inkbird Gateway."""

from __future__ import annotations

from pathlib import Path
from typing import Optional
import json
import logging

from .device_config import IntegrationConfig, DeviceConfig

_LOGGER = logging.getLogger(__name__)


class ConfigManager:
    """Manages loading and saving device configurations."""

    def __init__(self, config_dir: str | Path = "."):
        """Initialize configuration manager.

        Args:
            config_dir: Directory to look for configuration files.
        """
        self.config_dir = Path(config_dir)
        self.config_file = self.config_dir / "inkbird_config.json"

    def load_config(self) -> IntegrationConfig:
        """Load configuration from file.

        Returns:
            IntegrationConfig: Loaded configuration or empty config if file doesn't exist.
        """
        if not self.config_file.exists():
            _LOGGER.warning(
                f"Config file not found: {self.config_file}. Using defaults."
            )
            return IntegrationConfig()

        try:
            with open(self.config_file, "r") as f:
                config = IntegrationConfig.from_json(f.read())
                _LOGGER.info(f"Loaded {len(config.devices)} device(s) from {self.config_file}")
                return config
        except (json.JSONDecodeError, IOError) as e:
            _LOGGER.error(f"Failed to load config: {e}")
            return IntegrationConfig()

    def save_config(self, config: IntegrationConfig) -> bool:
        """Save configuration to file.

        Args:
            config: Configuration to save.

        Returns:
            bool: True if successful.
        """
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, "w") as f:
                f.write(config.to_json())
            _LOGGER.info(f"Saved {len(config.devices)} device(s) to {self.config_file}")
            return True
        except IOError as e:
            _LOGGER.error(f"Failed to save config: {e}")
            return False

    def create_example_config(self) -> IntegrationConfig:
        """Create and save an example configuration.

        Returns:
            IntegrationConfig: Example configuration.
        """
        config = IntegrationConfig()

        # Add example LAN device
        lan_device = DeviceConfig(
            device_id="abc123def456ghi789jk",
            local_key="a1b2c3d4e5f6g7h8i9j0",
            ip_address="192.168.188.40",
            protocol_version="3.3",
            use_lan=True,
            name="Living Room",
            model="IBS-M1S",
            channels=4,
            poll_interval=60,
            enabled=True,
        )
        config.add_device(lan_device)

        # Add example cloud-only device
        cloud_device = DeviceConfig(
            device_id="def456ghi789jk012lmn",
            access_id="your_tuya_access_id",
            access_secret="your_tuya_access_secret",
            use_lan=False,
            name="Remote Sensor",
            model="IBS-M1S",
            channels=4,
            poll_interval=60,
            enabled=False,  # Disabled by default until configured
        )
        config.add_device(cloud_device)

        return config


# Example configuration template
EXAMPLE_CONFIG_TEMPLATE = """{
  "devices": [
    {
      "device_id": "abc123def456ghi789jk",
      "local_key": "a1b2c3d4e5f6g7h8i9j0",
      "ip_address": "192.168.188.40",
      "protocol_version": "3.3",
      "use_lan": true,
      "access_id": null,
      "access_secret": null,
      "name": "Living Room",
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
