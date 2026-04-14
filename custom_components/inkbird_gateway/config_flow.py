"""Config flow for Inkbird Gateway."""

from __future__ import annotations

import asyncio
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import InkbirdGatewayApi, InkbirdGatewayApiAuthError, InkbirdGatewayApiError
from .const import (
    CONF_ACCESS_ID,
    CONF_ACCESS_SECRET,
    CONF_DEVICE_IDS,
    CONF_ENDPOINT,
    CONF_MANUAL_DEVICE_IDS,
    CONF_SCAN_INTERVAL,
    DEFAULT_ENDPOINT,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    ENDPOINT_OPTIONS,
    MAX_SCAN_INTERVAL,
    MIN_SCAN_INTERVAL,
)


class InkbirdGatewayConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Inkbird Gateway."""

    VERSION = 1

    def __init__(self) -> None:
        self._pending_input: dict[str, Any] = {}
        self._supported_devices: dict[str, str] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Handle the initial setup step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            endpoint = ENDPOINT_OPTIONS.get(user_input[CONF_ENDPOINT], user_input[CONF_ENDPOINT])
            pending_input = {
                CONF_ACCESS_ID: user_input[CONF_ACCESS_ID].strip(),
                CONF_ACCESS_SECRET: user_input[CONF_ACCESS_SECRET].strip(),
                CONF_ENDPOINT: endpoint.strip(),
                CONF_SCAN_INTERVAL: user_input[CONF_SCAN_INTERVAL],
            }

            await self.async_set_unique_id(
                f"{pending_input[CONF_ENDPOINT]}::{pending_input[CONF_ACCESS_ID]}"
            )
            self._abort_if_unique_id_configured()

            api = InkbirdGatewayApi(
                session=async_get_clientsession(self.hass),
                access_id=pending_input[CONF_ACCESS_ID],
                access_secret=pending_input[CONF_ACCESS_SECRET],
                endpoint=pending_input[CONF_ENDPOINT],
            )

            manual_device_ids = self._parse_manual_ids(
                user_input.get(CONF_MANUAL_DEVICE_IDS, "")
            )
            try:
                if manual_device_ids:
                    await asyncio.gather(
                        *(api.async_get_device_data(device_id) for device_id in manual_device_ids)
                    )
                    pending_input[CONF_DEVICE_IDS] = manual_device_ids
                    return self.async_create_entry(
                        title="Inkbird Gateway",
                        data=pending_input,
                    )

                devices = await api.async_get_supported_devices()
            except InkbirdGatewayApiAuthError:
                errors["base"] = "invalid_auth"
            except InkbirdGatewayApiError:
                errors["base"] = (
                    "invalid_device_ids" if manual_device_ids else "cannot_connect"
                )
            else:
                if not devices:
                    errors["base"] = "no_supported_devices"
                else:
                    self._pending_input = pending_input
                    self._supported_devices = {
                        device["id"]: f'{device["name"]} ({device["model"]})'
                        for device in devices
                    }
                    return await self.async_step_select_devices()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_ENDPOINT,
                        default=next(
                            (
                                key
                                for key, value in ENDPOINT_OPTIONS.items()
                                if value == DEFAULT_ENDPOINT
                            ),
                            DEFAULT_ENDPOINT,
                        ),
                    ): vol.In({**ENDPOINT_OPTIONS, DEFAULT_ENDPOINT: DEFAULT_ENDPOINT}),
                    vol.Required(CONF_ACCESS_ID): str,
                    vol.Required(CONF_ACCESS_SECRET): str,
                    vol.Optional(CONF_MANUAL_DEVICE_IDS, default=""): str,
                    vol.Required(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.All(
                        vol.Coerce(int),
                        vol.Range(min=MIN_SCAN_INTERVAL, max=MAX_SCAN_INTERVAL),
                    ),
                }
            ),
            errors=errors,
        )

    async def async_step_select_devices(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Select devices discovered for this account."""
        errors: dict[str, str] = {}
        if user_input is not None:
            selected_ids = list(user_input[CONF_DEVICE_IDS])
            if not selected_ids:
                errors["base"] = "no_supported_devices"
            else:
                payload = dict(self._pending_input)
                payload[CONF_DEVICE_IDS] = selected_ids
                return self.async_create_entry(title="Inkbird Gateway", data=payload)

        default_selection = list(self._supported_devices.keys())
        return self.async_show_form(
            step_id="select_devices",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_DEVICE_IDS, default=default_selection): cv.multi_select(
                        self._supported_devices
                    ),
                }
            ),
            errors=errors,
        )

    @staticmethod
    def _parse_manual_ids(raw_value: str) -> list[str]:
        return [item.strip() for item in raw_value.split(",") if item.strip()]
