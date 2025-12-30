"""Diagnostics support for Intesis Local."""
from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant

from .const import CONF_SCAN_INTERVAL, CONF_TEMP_STEP, DOMAIN
from .coordinator import IntesisDataUpdateCoordinator

TO_REDACT = {CONF_PASSWORD, CONF_USERNAME, "sessionID", "wlanSTAMAC", "wlanAPMAC", "sn"}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator: IntesisDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    return {
        "config": {
            CONF_HOST: entry.data.get(CONF_HOST),
            CONF_SCAN_INTERVAL: entry.options.get(CONF_SCAN_INTERVAL),
            CONF_TEMP_STEP: entry.options.get(CONF_TEMP_STEP),
        },
        "device_info": async_redact_data(coordinator.device_info, TO_REDACT),
        "datapoints": coordinator.data,
        "available": coordinator.available,
    }
