"""Base entity for Intesis Local integration."""
from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import IntesisDataUpdateCoordinator


class IntesisEntity(CoordinatorEntity[IntesisDataUpdateCoordinator]):
    """Base class for Intesis entities."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: IntesisDataUpdateCoordinator,
        unique_id_suffix: str,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)

        device_info = coordinator.device_info
        serial = device_info.get("sn", "unknown").split(" / ")[0]

        self._attr_unique_id = f"{serial}_{unique_id_suffix}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, serial)},
            name=f"Intesis {device_info.get('deviceModel', 'AC')}",
            manufacturer="Intesis",
            model=device_info.get("deviceModel", "Unknown"),
            sw_version=device_info.get("fwVersion", "Unknown"),
            configuration_url=f"http://{coordinator.api.host}/",
        )

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.coordinator.available and super().available
