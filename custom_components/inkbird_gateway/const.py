"""Constants for the Inkbird Gateway integration."""

from __future__ import annotations

from homeassistant.const import Platform

DOMAIN = "inkbird_gateway"

PLATFORMS: list[Platform] = [Platform.SENSOR]

CONF_ACCESS_ID = "access_id"
CONF_ACCESS_SECRET = "access_secret"
CONF_ENDPOINT = "endpoint"
CONF_DEVICE_IDS = "device_ids"
CONF_MANUAL_DEVICE_IDS = "manual_device_ids"
CONF_SCAN_INTERVAL = "scan_interval"

DEFAULT_SCAN_INTERVAL = 60
MIN_SCAN_INTERVAL = 30
MAX_SCAN_INTERVAL = 3600

DEFAULT_ENDPOINT = "https://openapi.tuyaus.com"
ENDPOINT_OPTIONS = {
    "US (openapi.tuyaus.com)": "https://openapi.tuyaus.com",
    "EU (openapi.tuyaeu.com)": "https://openapi.tuyaeu.com",
    "CN (openapi.tuyacn.com)": "https://openapi.tuyacn.com",
    "IN (openapi.tuyain.com)": "https://openapi.tuyain.com",
}

SUPPORTED_MODEL_MARKERS: tuple[str, ...] = ("ibs-m1", "ibs-m2")
SUPPORTED_TUYA_CATEGORY = "wsdcg"

