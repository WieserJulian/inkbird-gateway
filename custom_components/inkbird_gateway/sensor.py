"""Sensor platform for Inkbird Gateway."""

from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE, UnitOfTemperature
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import InkbirdGatewayConfigEntry
from .api import InkbirdChannelReading, InkbirdDeviceData
from .const import DOMAIN
from .coordinator import InkbirdGatewayCoordinator


async def async_setup_entry(
    hass,
    entry: InkbirdGatewayConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Inkbird sensors from config entry."""
    coordinator = entry.runtime_data.coordinator

    entities: list[InkbirdGatewaySensorEntity] = []
    for device_id, device in coordinator.data.items():
        for channel_index, channel in sorted(device.channels.items()):
            entities.extend(_build_channel_entities(coordinator, device_id, channel_index, channel))

    async_add_entities(entities)


def _build_channel_entities(
    coordinator: InkbirdGatewayCoordinator,
    device_id: str,
    channel_index: int,
    channel: InkbirdChannelReading,
) -> list["InkbirdGatewaySensorEntity"]:
    entities: list[InkbirdGatewaySensorEntity] = []
    if channel.temperature is not None:
        entities.append(
            InkbirdGatewaySensorEntity(
                coordinator=coordinator,
                device_id=device_id,
                channel_index=channel_index,
                metric="temperature",
            )
        )
    if channel.humidity is not None:
        entities.append(
            InkbirdGatewaySensorEntity(
                coordinator=coordinator,
                device_id=device_id,
                channel_index=channel_index,
                metric="humidity",
            )
        )
    if channel.battery is not None:
        entities.append(
            InkbirdGatewaySensorEntity(
                coordinator=coordinator,
                device_id=device_id,
                channel_index=channel_index,
                metric="battery",
            )
        )
    return entities


class InkbirdGatewaySensorEntity(
    CoordinatorEntity[InkbirdGatewayCoordinator], SensorEntity
):
    """Inkbird channel sensor."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: InkbirdGatewayCoordinator,
        device_id: str,
        channel_index: int,
        metric: str,
    ) -> None:
        super().__init__(coordinator)
        self._device_id = device_id
        self._channel_index = channel_index
        self._metric = metric

        channel_prefix = "Base station" if channel_index == 0 else f"Channel {channel_index}"
        metric_title = metric.capitalize()
        self._attr_name = f"{channel_prefix} {metric_title}"
        self._attr_unique_id = f"{device_id}_ch{channel_index}_{metric}"

        if metric == "temperature":
            self._attr_device_class = SensorDeviceClass.TEMPERATURE
            self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
            self._attr_state_class = SensorStateClass.MEASUREMENT
        elif metric == "humidity":
            self._attr_device_class = SensorDeviceClass.HUMIDITY
            self._attr_native_unit_of_measurement = PERCENTAGE
            self._attr_state_class = SensorStateClass.MEASUREMENT
        elif metric == "battery":
            self._attr_device_class = SensorDeviceClass.BATTERY
            self._attr_native_unit_of_measurement = PERCENTAGE
            self._attr_state_class = SensorStateClass.MEASUREMENT
            self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def native_value(self) -> float | int | None:
        """Return the current state value."""
        device = self.coordinator.data.get(self._device_id)
        if not device:
            return None
        channel = device.channels.get(self._channel_index)
        if not channel:
            return None
        return getattr(channel, self._metric)

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        device = self.coordinator.data.get(self._device_id)
        if not device:
            return False
        return device.online and self._channel_index in device.channels

    @property
    def device_info(self) -> DeviceInfo:
        """Describe the parent device."""
        device: InkbirdDeviceData | None = self.coordinator.data.get(self._device_id)
        if device is None:
            return DeviceInfo(
                identifiers={(DOMAIN, self._device_id)},
                manufacturer="Inkbird",
                name=self._device_id,
                model="Inkbird Gateway",
            )
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_id)},
            manufacturer="Inkbird",
            name=device.name,
            model=device.model,
            sw_version=device.sw_version,
        )

