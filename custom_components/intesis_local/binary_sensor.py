"""Binary sensor entities for Intesis Local integration."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, UID_ERROR_CODE
from .coordinator import IntesisDataUpdateCoordinator
from .entity import IntesisEntity


@dataclass(frozen=True)
class IntesisBinarySensorEntityDescription(BinarySensorEntityDescription):
    """Describes an Intesis binary sensor entity."""

    is_on_fn: Callable[[IntesisDataUpdateCoordinator], bool | None] | None = None


BINARY_SENSOR_DESCRIPTIONS: tuple[IntesisBinarySensorEntityDescription, ...] = (
    IntesisBinarySensorEntityDescription(
        key="ac_connection",
        translation_key="ac_connection",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        is_on_fn=lambda c: c.device_info.get("acStatus", 0) == 1,
    ),
    IntesisBinarySensorEntityDescription(
        key="wifi_connection",
        translation_key="wifi_connection",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        entity_registry_enabled_default=False,
        is_on_fn=lambda c: c.device_info.get("wlanLNK", 0) == 1,
    ),
    IntesisBinarySensorEntityDescription(
        key="cloud_connection",
        translation_key="cloud_connection",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        entity_registry_enabled_default=False,
        is_on_fn=lambda c: c.device_info.get("tcpServerLNK", 0) == 1,
    ),
    IntesisBinarySensorEntityDescription(
        key="error",
        translation_key="error",
        device_class=BinarySensorDeviceClass.PROBLEM,
        is_on_fn=lambda c: (
            c.device_info.get("lastError", 0) != 0
            or c.get_value(UID_ERROR_CODE, 0) != 0
        ),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Intesis binary sensor entities."""
    coordinator: IntesisDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        IntesisBinarySensor(coordinator, description)
        for description in BINARY_SENSOR_DESCRIPTIONS
    )


class IntesisBinarySensor(IntesisEntity, BinarySensorEntity):
    """Intesis binary sensor entity."""

    entity_description: IntesisBinarySensorEntityDescription

    def __init__(
        self,
        coordinator: IntesisDataUpdateCoordinator,
        description: IntesisBinarySensorEntityDescription,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def is_on(self) -> bool | None:
        """Return True if the binary sensor is on."""
        if self.entity_description.is_on_fn is not None:
            return self.entity_description.is_on_fn(self.coordinator)
        return None
