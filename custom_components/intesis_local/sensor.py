"""Sensor entities for Intesis Local integration."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, UID_CURRENT_TEMP, UID_MAX_TEMP, UID_MIN_TEMP
from .coordinator import IntesisDataUpdateCoordinator
from .entity import IntesisEntity


@dataclass(frozen=True)
class IntesisSensorEntityDescription(SensorEntityDescription):
    """Describes an Intesis sensor entity."""

    value_fn: Callable[[IntesisDataUpdateCoordinator], Any] | None = None


SENSOR_DESCRIPTIONS: tuple[IntesisSensorEntityDescription, ...] = (
    IntesisSensorEntityDescription(
        key="current_temperature",
        translation_key="current_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value_fn=lambda c: c.get_value(UID_CURRENT_TEMP, 0) / 10
        if c.get_value(UID_CURRENT_TEMP) is not None
        else None,
    ),
    IntesisSensorEntityDescription(
        key="wifi_signal",
        translation_key="wifi_signal",
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
        entity_registry_enabled_default=False,
        value_fn=lambda c: c.device_info.get("rssi"),
    ),
    IntesisSensorEntityDescription(
        key="min_temp_limit",
        translation_key="min_temp_limit",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        entity_registry_enabled_default=False,
        value_fn=lambda c: c.get_value(UID_MIN_TEMP, 160) / 10
        if c.get_value(UID_MIN_TEMP) is not None
        else None,
    ),
    IntesisSensorEntityDescription(
        key="max_temp_limit",
        translation_key="max_temp_limit",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        entity_registry_enabled_default=False,
        value_fn=lambda c: c.get_value(UID_MAX_TEMP, 300) / 10
        if c.get_value(UID_MAX_TEMP) is not None
        else None,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Intesis sensor entities."""
    coordinator: IntesisDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        IntesisSensor(coordinator, description) for description in SENSOR_DESCRIPTIONS
    )


class IntesisSensor(IntesisEntity, SensorEntity):
    """Intesis sensor entity."""

    entity_description: IntesisSensorEntityDescription

    def __init__(
        self,
        coordinator: IntesisDataUpdateCoordinator,
        description: IntesisSensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> Any:
        """Return the sensor value."""
        if self.entity_description.value_fn is not None:
            return self.entity_description.value_fn(self.coordinator)
        return None
