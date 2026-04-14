"""Tuya OpenAPI client for Inkbird Gateway devices."""

from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import json
import logging
import struct
import time
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode

from aiohttp import ClientError, ClientSession

from .const import SUPPORTED_MODEL_MARKERS, SUPPORTED_TUYA_CATEGORY

_LOGGER = logging.getLogger(__name__)

_TOKEN_GRACE_SECONDS = 60
_AUTH_ERROR_CODES = {"1010", "1011", "1012", "1106"}


def _has_cjk_chars(value: str) -> bool:
    """Return True when text contains CJK characters."""
    return any(
        "\u4e00" <= char <= "\u9fff"
        or "\u3400" <= char <= "\u4dbf"
        or "\uf900" <= char <= "\ufaff"
        for char in value
    )


def _friendly_device_name(device_id: str, name: str, model: str) -> str:
    """Return a user-friendly name with German-friendly fallback."""
    cleaned_name = name.strip()
    cleaned_model = model.strip()

    if cleaned_name and not _has_cjk_chars(cleaned_name):
        return cleaned_name

    if cleaned_model and not _has_cjk_chars(cleaned_model):
        suffix = device_id[-4:] if len(device_id) >= 4 else device_id
        return f"{cleaned_model} Gerät {suffix}".strip()

    suffix = device_id[-6:] if len(device_id) >= 6 else device_id
    return f"Inkbird Gerät {suffix}".strip()


class InkbirdGatewayApiError(Exception):
    """Base API error."""


class InkbirdGatewayApiAuthError(InkbirdGatewayApiError):
    """Authentication failure."""


@dataclass(slots=True, frozen=True)
class InkbirdChannelReading:
    """Single channel readings for an Inkbird device."""

    temperature: float | None = None
    humidity: float | None = None
    battery: int | None = None


@dataclass(slots=True, frozen=True)
class InkbirdDeviceData:
    """Parsed Inkbird device state."""

    device_id: str
    name: str
    model: str
    sw_version: str | None
    online: bool
    channels: dict[int, InkbirdChannelReading]


class InkbirdGatewayApi:
    """Small Tuya OpenAPI client for Inkbird data."""

    def __init__(
        self,
        session: ClientSession,
        access_id: str,
        access_secret: str,
        endpoint: str,
    ) -> None:
        self._session = session
        self._access_id = access_id
        self._access_secret = access_secret
        self._endpoint = endpoint.rstrip("/")

        self._token: str | None = None
        self._uid: str | None = None
        self._token_expires_at: float = 0

    async def async_get_supported_devices(self) -> list[dict[str, str]]:
        """Return discoverable IBS-M1/IBS-M2 devices for this account."""
        await self._async_ensure_token()
        if not self._uid:
            raise InkbirdGatewayApiAuthError("Token response did not include user id")

        response = await self._async_request("GET", f"/v1.0/users/{self._uid}/devices")
        raw_devices = response.get("result") or []

        devices: list[dict[str, str]] = []
        for device in raw_devices:
            if not self._is_supported_device(device):
                continue

            device_id = str(device.get("id", "")).strip()
            if not device_id:
                continue
            raw_name = str(device.get("name") or "")
            model = str(
                device.get("product_name")
                or device.get("model")
                or device.get("category")
                or "Inkbird"
            )
            name = _friendly_device_name(device_id, raw_name, model)
            devices.append({"id": device_id, "name": name, "model": model})

        return devices

    async def async_get_device_data(self, device_id: str) -> InkbirdDeviceData:
        """Fetch and parse a single device payload."""
        response = await self._async_request("GET", f"/v1.0/devices/{device_id}")
        payload = response.get("result")
        if not isinstance(payload, dict):
            raise InkbirdGatewayApiError(
                f"Unexpected payload for {device_id}: missing result object"
            )
        return self._parse_device_payload(device_id, payload)

    async def _async_ensure_token(self) -> None:
        if self._token and time.time() < (self._token_expires_at - _TOKEN_GRACE_SECONDS):
            return
        await self._async_authenticate()

    async def _async_authenticate(self) -> None:
        response = await self._async_request(
            "GET",
            "/v1.0/token",
            params={"grant_type": 1},
            use_token=False,
        )
        result = response.get("result")
        if not isinstance(result, dict):
            raise InkbirdGatewayApiAuthError("Invalid token response")

        token = result.get("access_token")
        if not isinstance(token, str) or not token:
            raise InkbirdGatewayApiAuthError("Missing access token in response")

        expire_time = int(result.get("expire_time", 3600))
        self._token = token
        self._uid = result.get("uid")
        self._token_expires_at = time.time() + expire_time

    async def _async_request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        body: dict[str, Any] | None = None,
        use_token: bool = True,
        _retry_on_auth_error: bool = True,
    ) -> dict[str, Any]:
        if use_token:
            await self._async_ensure_token()

        body_string = json.dumps(body, separators=(",", ":"), ensure_ascii=True) if body else ""
        query_string = urlencode(sorted((params or {}).items()), doseq=True)
        signed_path = f"{path}?{query_string}" if query_string else path

        timestamp = str(int(time.time() * 1000))
        content_hash = hashlib.sha256(body_string.encode("utf-8")).hexdigest()
        string_to_sign = "\n".join([method.upper(), content_hash, "", signed_path])
        sign_input = (
            f"{self._access_id}{self._token}{timestamp}{string_to_sign}"
            if use_token
            else f"{self._access_id}{timestamp}{string_to_sign}"
        )
        sign = (
            hmac.new(
                self._access_secret.encode("utf-8"),
                sign_input.encode("utf-8"),
                hashlib.sha256,
            )
            .hexdigest()
            .upper()
        )

        headers = {
            "client_id": self._access_id,
            "sign": sign,
            "sign_method": "HMAC-SHA256",
            "t": timestamp,
        }
        if use_token and self._token:
            headers["access_token"] = self._token

        request_url = f"{self._endpoint}{path}"
        try:
            async with self._session.request(
                method,
                request_url,
                headers=headers,
                params=params,
                json=body,
            ) as response:
                text = await response.text()
        except ClientError as err:
            raise InkbirdGatewayApiError(f"Network error calling Tuya API: {err}") from err

        try:
            data = json.loads(text)
        except json.JSONDecodeError as err:
            raise InkbirdGatewayApiError(
                f"Invalid response from Tuya endpoint {path}: {text[:200]}"
            ) from err

        if data.get("success"):
            return data

        code = str(data.get("code", ""))
        message = str(data.get("msg", "Unknown Tuya API error"))

        if use_token and _retry_on_auth_error and code in _AUTH_ERROR_CODES:
            _LOGGER.debug("Token rejected by Tuya (%s), refreshing token", code)
            await self._async_authenticate()
            return await self._async_request(
                method,
                path,
                params=params,
                body=body,
                use_token=use_token,
                _retry_on_auth_error=False,
            )

        if code in _AUTH_ERROR_CODES:
            raise InkbirdGatewayApiAuthError(message)
        raise InkbirdGatewayApiError(f"Tuya API error {code}: {message}")

    @staticmethod
    def _is_supported_device(device: dict[str, Any]) -> bool:
        text = " ".join(
            str(device.get(key, "")).lower()
            for key in ("name", "product_name", "model", "category")
        )
        if any(marker in text for marker in SUPPORTED_MODEL_MARKERS):
            return True
        return str(device.get("category", "")).lower() == SUPPORTED_TUYA_CATEGORY

    def _parse_device_payload(
        self, device_id: str, payload: dict[str, Any]
    ) -> InkbirdDeviceData:
        status_items = payload.get("status") or []
        status_map = {
            str(item["code"]): item.get("value")
            for item in status_items
            if isinstance(item, dict) and "code" in item
        }
        scales = self._extract_scales(payload.get("status_range") or [])

        channels: dict[int, InkbirdChannelReading] = {}
        for code, value in status_map.items():
            if not (code.startswith("ch_") and len(code) == 4 and code[-1].isdigit()):
                continue
            if not isinstance(value, str):
                continue
            channel_index = int(code[-1])
            parsed = self._decode_channel(value)
            if parsed is not None:
                channels[channel_index] = parsed

        fallback_temperature = self._first_scaled_value(
            status_map,
            scales,
            ("va_temperature", "temp_current", "temperature"),
        )
        fallback_humidity = self._first_scaled_value(
            status_map,
            scales,
            ("va_humidity", "humidity_value", "humidity"),
        )
        fallback_battery = self._first_battery_value(
            status_map,
            ("battery_percentage", "battery_value", "va_battery"),
        )

        if any(v is not None for v in (fallback_temperature, fallback_humidity, fallback_battery)):
            existing = channels.get(0, InkbirdChannelReading())
            channels[0] = InkbirdChannelReading(
                temperature=(
                    existing.temperature
                    if existing.temperature is not None
                    else fallback_temperature
                ),
                humidity=(
                    existing.humidity if existing.humidity is not None else fallback_humidity
                ),
                battery=existing.battery if existing.battery is not None else fallback_battery,
            )

        model = str(payload.get("product_name") or payload.get("model") or "Inkbird Gateway")
        name = _friendly_device_name(device_id, str(payload.get("name") or ""), model)

        return InkbirdDeviceData(
            device_id=device_id,
            name=name,
            model=model,
            sw_version=(str(payload.get("pv")) if payload.get("pv") else None),
            online=bool(payload.get("online", True)),
            channels=channels,
        )

    @staticmethod
    def _extract_scales(status_ranges: list[dict[str, Any]]) -> dict[str, int]:
        scales: dict[str, int] = {}
        for item in status_ranges:
            if not isinstance(item, dict):
                continue
            code = item.get("code")
            values = item.get("values")
            if not code or not isinstance(values, str):
                continue
            try:
                parsed_values = json.loads(values)
            except json.JSONDecodeError:
                continue
            scale = parsed_values.get("scale")
            if isinstance(scale, int):
                scales[str(code)] = scale
        return scales

    @staticmethod
    def _first_scaled_value(
        status_map: dict[str, Any], scales: dict[str, int], keys: tuple[str, ...]
    ) -> float | None:
        for key in keys:
            raw = status_map.get(key)
            if raw is None:
                continue
            if not isinstance(raw, (int, float, str)):
                continue
            try:
                numeric = float(raw)
            except ValueError:
                continue
            scale = scales.get(key, 0)
            value = numeric / (10**scale)
            return round(value, 1)
        return None

    @staticmethod
    def _first_battery_value(
        status_map: dict[str, Any], keys: tuple[str, ...]
    ) -> int | None:
        for key in keys:
            raw = status_map.get(key)
            if raw is None:
                continue
            if not isinstance(raw, (int, float, str)):
                continue
            try:
                value = int(float(raw))
            except ValueError:
                continue
            if 0 <= value <= 100:
                return value
        return None

    @staticmethod
    def _decode_channel(raw: str) -> InkbirdChannelReading | None:
        try:
            decoded = base64.b64decode(raw, validate=False)
        except binascii.Error:
            return None

        # Parser reads bytes [1:11] and unpacks "<hHIb" (9 bytes),
        # so 10 decoded bytes are the minimal valid payload.
        if len(decoded) < 10:
            return None

        try:
            temperature_raw, humidity_raw, _, battery_raw = struct.Struct("<hHIb").unpack(
                decoded[1:11]
            )
        except struct.error:
            return None

        temperature = round(temperature_raw / 10, 1)
        humidity = round(humidity_raw / 10, 1)
        battery = int(battery_raw)

        if humidity < 0 or humidity > 100:
            humidity = None
        if battery < 0 or battery > 100:
            battery = None

        return InkbirdChannelReading(
            temperature=temperature,
            humidity=humidity,
            battery=battery,
        )
