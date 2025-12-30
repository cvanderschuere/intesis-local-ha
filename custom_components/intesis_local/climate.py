"""Climate entity for Intesis Local integration."""
from __future__ import annotations

import asyncio
import logging
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
    PRESET_MODE_MAP,
    PRESET_MODE_TO_DEVICE,
    UID_CURRENT_TEMP,
    UID_FAN_SPEED,
    UID_MAX_TEMP,
    UID_MIN_TEMP,
    UID_MODE,
    UID_POWER,
    UID_QUIET_MODE,
    UID_SETPOINT,
    UID_VANE_HORIZONTAL,
    UID_VANE_VERTICAL,
    VANE_VERTICAL_MAP,
    VANE_VERTICAL_TO_DEVICE,
)
from .coordinator import IntesisDataUpdateCoordinator
from .entity import IntesisEntity

_LOGGER = logging.getLogger(__name__)


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
        | ClimateEntityFeature.PRESET_MODE
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
        self._attr_preset_modes = list(PRESET_MODE_MAP.values())

        # Set temperature step from options
        self._attr_target_temperature_step = entry.options.get(
            CONF_TEMP_STEP, DEFAULT_TEMP_STEP
        )

        # Optimistic state for immediate UI feedback
        self._optimistic_target_temp: float | None = None
        self._optimistic_hvac_mode: HVACMode | None = None
        self._optimistic_fan_mode: str | None = None
        self._optimistic_swing_mode: str | None = None
        self._optimistic_preset_mode: str | None = None

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
        if self._optimistic_target_temp is not None:
            return self._optimistic_target_temp

        temp = self.coordinator.get_value(UID_SETPOINT)
        return temp / 10 if temp is not None else None

    @property
    def hvac_mode(self) -> HVACMode:
        """Return the current HVAC mode."""
        if self._optimistic_hvac_mode is not None:
            return self._optimistic_hvac_mode

        power = self.coordinator.get_value(UID_POWER, 0)
        if power == 0:
            return HVACMode.OFF

        mode = self.coordinator.get_value(UID_MODE, 0)
        return HVAC_MODE_MAP.get(mode, HVACMode.AUTO)

    @property
    def fan_mode(self) -> str | None:
        """Return the current fan mode."""
        if self._optimistic_fan_mode is not None:
            return self._optimistic_fan_mode

        fan = self.coordinator.get_value(UID_FAN_SPEED, 0)
        return FAN_MODE_MAP.get(fan)

    @property
    def swing_mode(self) -> str | None:
        """Return the current swing mode (vertical vane)."""
        if self._optimistic_swing_mode is not None:
            return self._optimistic_swing_mode

        vane = self.coordinator.get_value(UID_VANE_VERTICAL, 0)
        return VANE_VERTICAL_MAP.get(vane)

    @property
    def preset_mode(self) -> str | None:
        """Return the current preset mode."""
        if self._optimistic_preset_mode is not None:
            return self._optimistic_preset_mode

        preset = self.coordinator.get_value(UID_QUIET_MODE, 0)
        return PRESET_MODE_MAP.get(preset)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        # Clear optimistic state when real data arrives
        self._optimistic_target_temp = None
        self._optimistic_hvac_mode = None
        self._optimistic_fan_mode = None
        self._optimistic_swing_mode = None
        self._optimistic_preset_mode = None
        super()._handle_coordinator_update()

    async def _async_set_with_verification(
        self,
        uid: int,
        value: int,
        delay: float = 2.0,
    ) -> None:
        """Set a value and schedule verification refresh."""
        await self.coordinator.async_set_datapoint(uid, value)

        # Schedule verification after delay
        async def verify() -> None:
            await asyncio.sleep(delay)
            await self.coordinator.async_request_refresh()

        self.hass.async_create_task(verify())

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        temp = kwargs.get(ATTR_TEMPERATURE)
        if temp is None:
            return

        # Optimistic update for immediate UI feedback
        self._optimistic_target_temp = temp
        self.async_write_ha_state()

        # Send to device with verification
        await self._async_set_with_verification(UID_SETPOINT, int(temp * 10))

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new HVAC mode."""
        # Optimistic update
        self._optimistic_hvac_mode = hvac_mode
        self.async_write_ha_state()

        if hvac_mode == HVACMode.OFF:
            await self._async_set_with_verification(UID_POWER, 0)
        else:
            # Turn on if needed, then set mode
            if self.coordinator.get_value(UID_POWER, 0) == 0:
                await self.coordinator.async_set_datapoint(UID_POWER, 1)

            device_mode = HVAC_MODE_TO_DEVICE.get(hvac_mode, 0)
            await self._async_set_with_verification(UID_MODE, device_mode)

    async def async_set_fan_mode(self, fan_mode: str) -> None:
        """Set new fan mode."""
        # Optimistic update
        self._optimistic_fan_mode = fan_mode
        self.async_write_ha_state()

        device_fan = FAN_MODE_TO_DEVICE.get(fan_mode, 0)
        await self._async_set_with_verification(UID_FAN_SPEED, device_fan)

    async def async_set_swing_mode(self, swing_mode: str) -> None:
        """Set new swing mode (vertical vane)."""
        # Optimistic update
        self._optimistic_swing_mode = swing_mode
        self.async_write_ha_state()

        device_swing = VANE_VERTICAL_TO_DEVICE.get(swing_mode, 0)
        await self._async_set_with_verification(UID_VANE_VERTICAL, device_swing)

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set new preset mode."""
        # Optimistic update
        self._optimistic_preset_mode = preset_mode
        self.async_write_ha_state()

        device_preset = PRESET_MODE_TO_DEVICE.get(preset_mode, 0)
        await self._async_set_with_verification(UID_QUIET_MODE, device_preset)

    async def async_turn_on(self) -> None:
        """Turn on the AC."""
        self._optimistic_hvac_mode = HVACMode.AUTO
        self.async_write_ha_state()
        await self._async_set_with_verification(UID_POWER, 1)

    async def async_turn_off(self) -> None:
        """Turn off the AC."""
        self._optimistic_hvac_mode = HVACMode.OFF
        self.async_write_ha_state()
        await self._async_set_with_verification(UID_POWER, 0)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        vane_h = self.coordinator.get_value(UID_VANE_HORIZONTAL, 0)

        return {
            "horizontal_vane": vane_h,
            "horizontal_swing": vane_h == 10,
        }
