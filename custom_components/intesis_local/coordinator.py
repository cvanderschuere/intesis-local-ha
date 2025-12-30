"""DataUpdateCoordinator for Intesis Local integration."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import IntesisConnectionError, IntesisError, IntesisLocalAPI
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class IntesisDataUpdateCoordinator(DataUpdateCoordinator[dict[int, int]]):
    """Class to manage fetching Intesis data."""

    def __init__(
        self,
        hass: HomeAssistant,
        api: IntesisLocalAPI,
        update_interval: int,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=update_interval),
        )
        self.api = api
        self.device_info: dict[str, Any] = {}
        self._available = True

    @property
    def available(self) -> bool:
        """Return True if device is available."""
        return self._available

    async def _async_update_data(self) -> dict[int, int]:
        """Fetch data from the device."""
        try:
            # Fetch datapoints
            datapoints = await self.api.get_all_datapoints()

            # Also refresh device info periodically
            self.device_info = await self.api.get_info()

            self._available = True

            # Convert to dict keyed by UID
            return {dp["uid"]: dp["value"] for dp in datapoints}

        except IntesisConnectionError as err:
            self._available = False
            raise UpdateFailed(f"Connection error: {err}") from err
        except IntesisError as err:
            raise UpdateFailed(f"Error fetching data: {err}") from err

    async def async_set_datapoint(self, uid: int, value: int) -> None:
        """Set a datapoint value and refresh data."""
        try:
            await self.api.set_datapoint(uid, value)
        except (IntesisConnectionError, IntesisError) as err:
            _LOGGER.error("Failed to set datapoint %d: %s", uid, err)
            raise

    def get_value(self, uid: int, default: int | None = None) -> int | None:
        """Get a datapoint value from the current data."""
        if self.data is None:
            return default
        return self.data.get(uid, default)
