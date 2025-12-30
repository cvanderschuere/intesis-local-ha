"""Climate entity for Intesis Local integration."""
from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Any

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_TEMP_STEP,
    DEFAULT_TEMP_STEP,
    DOMAIN,
    FAN_MODE_MAP,
    FAN_MODE_TO_DEVICE,
    HVAC_MODE_MAP,
    HVAC_MODE_TO_DEVICE,
    UID_CURRENT_TEMP,
    UID_FAN_SPEED,
    UID_MAX_TEMP,
    UID_MIN_TEMP,
    UID_MODE,
    UID_POWER,
    UID_SETPOINT,
    UID_VANE_HORIZONTAL,
    UID_VANE_VERTICAL,
    VANE_VERTICAL_MAP,
    VANE_VERTICAL_TO_DEVICE,
)
from .coordinator import IntesisDataUpdateCoordinator
from .entity import IntesisEntity

_LOGGER = logging.getLogger(__name__)

# How long to hold pending changes before accepting device value (seconds)
PENDING_TIMEOUT = 15.0


@dataclass
class PendingChange:
    """Represents a pending change waiting for device confirmation."""

    value: Any
    device_value: int  # The value we sent to the device
    timestamp: float

    def is_expired(self) -> bool:
        """Check if this pending change has expired."""
        return time.monotonic() - self.timestamp > PENDING_TIMEOUT


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Intesis climate entity."""
    coordinator: IntesisDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities([IntesisClimate(coordinator, entry)])


class IntesisClimate(IntesisEntity, ClimateEntity):
    """Intesis climate entity."""

    _attr_name = None  # Use device name
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.FAN_MODE
        | ClimateEntityFeature.SWING_MODE
        | ClimateEntityFeature.TURN_OFF
        | ClimateEntityFeature.TURN_ON
    )
    _enable_turn_on_off_backwards_compat = False

    def __init__(
        self,
        coordinator: IntesisDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the climate entity."""
        super().__init__(coordinator, "climate")

        self._entry = entry

        # Build supported modes from device capabilities
        self._attr_hvac_modes = [HVACMode.OFF] + list(HVAC_MODE_MAP.values())
        self._attr_fan_modes = list(FAN_MODE_MAP.values())
        self._attr_swing_modes = list(VANE_VERTICAL_MAP.values())

        # Set temperature step from options
        self._attr_target_temperature_step = entry.options.get(
            CONF_TEMP_STEP, DEFAULT_TEMP_STEP
        )

        # Pending changes - keyed by UID or special key
        # These hold the value we want until device confirms or timeout
        self._pending: dict[str, PendingChange] = {}

    def _set_pending(self, key: str, value: Any, device_value: int) -> None:
        """Set a pending change."""
        self._pending[key] = PendingChange(
            value=value,
            device_value=device_value,
            timestamp=time.monotonic(),
        )
        _LOGGER.debug("Set pending %s = %s (device: %d)", key, value, device_value)

    def _get_pending(self, key: str) -> Any | None:
        """Get a pending value if it exists and hasn't expired."""
        if key not in self._pending:
            return None

        pending = self._pending[key]
        if pending.is_expired():
            _LOGGER.debug("Pending %s expired, clearing", key)
            del self._pending[key]
            return None

        return pending.value

    def _check_pending_confirmed(self, key: str, uid: int) -> bool:
        """Check if a pending change has been confirmed by the device."""
        if key not in self._pending:
            return True  # No pending change

        pending = self._pending[key]
        device_value = self.coordinator.get_value(uid)

        if device_value == pending.device_value:
            # Device confirmed the change
            _LOGGER.debug("Pending %s confirmed by device (value: %d)", key, device_value)
            del self._pending[key]
            return True

        if pending.is_expired():
            # Timeout - accept device value
            _LOGGER.debug("Pending %s timed out, accepting device value", key)
            del self._pending[key]
            return True

        # Still waiting for confirmation
        return False

    @property
    def min_temp(self) -> float:
        """Return the minimum temperature."""
        min_val = self.coordinator.get_value(UID_MIN_TEMP, 160)
        return min_val / 10 if min_val else 16.0

    @property
    def max_temp(self) -> float:
        """Return the maximum temperature."""
        max_val = self.coordinator.get_value(UID_MAX_TEMP, 300)
        return max_val / 10 if max_val else 30.0

    @property
    def current_temperature(self) -> float | None:
        """Return the current temperature."""
        temp = self.coordinator.get_value(UID_CURRENT_TEMP)
        return temp / 10 if temp is not None else None

    @property
    def target_temperature(self) -> float | None:
        """Return the target temperature."""
        # Check for pending change first
        pending = self._get_pending("target_temp")
        if pending is not None:
            return pending

        temp = self.coordinator.get_value(UID_SETPOINT)
        if temp is None:
            return None
        # Sentinel 32768 (0x8000) means "not set", also reject unreasonable values
        if temp == 32768 or temp > 500 or temp < 0:
            return None
        return temp / 10

    @property
    def hvac_mode(self) -> HVACMode:
        """Return the current HVAC mode."""
        # Check for pending change first
        pending = self._get_pending("hvac_mode")
        if pending is not None:
            return pending

        power = self.coordinator.get_value(UID_POWER, 0)
        if power == 0:
            return HVACMode.OFF

        mode = self.coordinator.get_value(UID_MODE, 0)
        return HVAC_MODE_MAP.get(mode, HVACMode.AUTO)

    @property
    def fan_mode(self) -> str | None:
        """Return the current fan mode."""
        pending = self._get_pending("fan_mode")
        if pending is not None:
            return pending

        fan = self.coordinator.get_value(UID_FAN_SPEED, 0)
        return FAN_MODE_MAP.get(fan)

    @property
    def swing_mode(self) -> str | None:
        """Return the current swing mode (vertical vane)."""
        pending = self._get_pending("swing_mode")
        if pending is not None:
            return pending

        vane = self.coordinator.get_value(UID_VANE_VERTICAL, 0)
        return VANE_VERTICAL_MAP.get(vane)


    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        # Check each pending change to see if device confirmed it
        # Only clear if confirmed or expired
        self._check_pending_confirmed("target_temp", UID_SETPOINT)
        self._check_pending_confirmed("fan_mode", UID_FAN_SPEED)
        self._check_pending_confirmed("swing_mode", UID_VANE_VERTICAL)

        # HVAC mode is special - check both power and mode
        if "hvac_mode" in self._pending:
            pending = self._pending["hvac_mode"]
            if pending.value == HVACMode.OFF:
                # Waiting for power off
                if self.coordinator.get_value(UID_POWER, 0) == 0:
                    del self._pending["hvac_mode"]
                elif pending.is_expired():
                    del self._pending["hvac_mode"]
            else:
                # Waiting for mode change
                self._check_pending_confirmed("hvac_mode", UID_MODE)

        super()._handle_coordinator_update()

    async def _async_send_command(self, uid: int, value: int) -> None:
        """Send command to device and schedule refresh."""
        await self.coordinator.async_set_datapoint(uid, value)

        # Schedule a refresh after a short delay to check confirmation
        async def refresh_after_delay() -> None:
            await asyncio.sleep(3)
            await self.coordinator.async_request_refresh()

        self.hass.async_create_task(refresh_after_delay())

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        temp = kwargs.get(ATTR_TEMPERATURE)
        if temp is None:
            return

        device_value = int(temp * 10)

        # Set pending change
        self._set_pending("target_temp", temp, device_value)
        self.async_write_ha_state()

        # Send to device
        await self._async_send_command(UID_SETPOINT, device_value)

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new HVAC mode."""
        if hvac_mode == HVACMode.OFF:
            device_value = 0  # Power off
            self._set_pending("hvac_mode", hvac_mode, device_value)
            self.async_write_ha_state()
            await self._async_send_command(UID_POWER, 0)
        else:
            device_value = HVAC_MODE_TO_DEVICE.get(hvac_mode, 0)
            self._set_pending("hvac_mode", hvac_mode, device_value)
            self.async_write_ha_state()

            # Turn on if needed, then set mode
            if self.coordinator.get_value(UID_POWER, 0) == 0:
                await self.coordinator.async_set_datapoint(UID_POWER, 1)

            await self._async_send_command(UID_MODE, device_value)

    async def async_set_fan_mode(self, fan_mode: str) -> None:
        """Set new fan mode."""
        device_value = FAN_MODE_TO_DEVICE.get(fan_mode, 0)
        self._set_pending("fan_mode", fan_mode, device_value)
        self.async_write_ha_state()

        await self._async_send_command(UID_FAN_SPEED, device_value)

    async def async_set_swing_mode(self, swing_mode: str) -> None:
        """Set new swing mode (vertical vane)."""
        device_value = VANE_VERTICAL_TO_DEVICE.get(swing_mode, 0)
        self._set_pending("swing_mode", swing_mode, device_value)
        self.async_write_ha_state()

        await self._async_send_command(UID_VANE_VERTICAL, device_value)

    async def async_turn_on(self) -> None:
        """Turn on the AC."""
        # Set to AUTO mode when turning on
        self._set_pending("hvac_mode", HVACMode.AUTO, 0)
        self.async_write_ha_state()
        await self._async_send_command(UID_POWER, 1)

    async def async_turn_off(self) -> None:
        """Turn off the AC."""
        self._set_pending("hvac_mode", HVACMode.OFF, 0)
        self.async_write_ha_state()
        await self._async_send_command(UID_POWER, 0)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        vane_h = self.coordinator.get_value(UID_VANE_HORIZONTAL, 0)

        # Include pending changes count for debugging
        pending_count = len(self._pending)

        attrs = {
            "horizontal_vane": vane_h,
            "horizontal_swing": vane_h == 10,
        }

        if pending_count > 0:
            attrs["pending_changes"] = pending_count

        return attrs
