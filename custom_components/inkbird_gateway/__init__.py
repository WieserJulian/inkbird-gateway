"""Inkbird Gateway Home Assistant integration."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import InkbirdGatewayApi
from .const import (
    CONF_ACCESS_ID,
    CONF_ACCESS_SECRET,
    CONF_DEVICE_IDS,
    CONF_ENDPOINT,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    PLATFORMS,
)
from .coordinator import InkbirdGatewayCoordinator


@dataclass(slots=True)
class InkbirdGatewayRuntimeData:
    """Runtime data for a config entry."""

    api: InkbirdGatewayApi
    coordinator: InkbirdGatewayCoordinator


type InkbirdGatewayConfigEntry = ConfigEntry[InkbirdGatewayRuntimeData]


async def async_setup_entry(hass: HomeAssistant, entry: InkbirdGatewayConfigEntry) -> bool:
    """Set up Inkbird Gateway from a config entry."""
    session = async_get_clientsession(hass)

    api = InkbirdGatewayApi(
        session=session,
        access_id=entry.data[CONF_ACCESS_ID],
        access_secret=entry.data[CONF_ACCESS_SECRET],
        endpoint=entry.data[CONF_ENDPOINT],
    )
    coordinator = InkbirdGatewayCoordinator(
        hass=hass,
        api=api,
        device_ids=list(entry.data[CONF_DEVICE_IDS]),
        scan_interval_seconds=entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
    )
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = InkbirdGatewayRuntimeData(api=api, coordinator=coordinator)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: InkbirdGatewayConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

