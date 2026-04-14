"""Data coordinator for Inkbird Gateway devices."""

from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import InkbirdDeviceData, InkbirdGatewayApi, InkbirdGatewayApiError
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class InkbirdGatewayCoordinator(DataUpdateCoordinator[dict[str, InkbirdDeviceData]]):
    """Coordinate state polling for configured Inkbird devices."""

    def __init__(
        self,
        hass: HomeAssistant,
        api: InkbirdGatewayApi,
        device_ids: list[str],
        scan_interval_seconds: int,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval_seconds),
        )
        self._api = api
        self._device_ids = device_ids

    async def _async_update_data(self) -> dict[str, InkbirdDeviceData]:
        devices: dict[str, InkbirdDeviceData] = {}
        errors: list[str] = []

        for device_id in self._device_ids:
            try:
                devices[device_id] = await self._api.async_get_device_data(device_id)
            except InkbirdGatewayApiError as err:
                errors.append(f"{device_id}: {err}")

        if not devices:
            raise UpdateFailed(
                "Unable to update any configured Inkbird device: " + "; ".join(errors)
            )

        if errors:
            _LOGGER.warning("Partial Inkbird update failure: %s", "; ".join(errors))

        return devices

