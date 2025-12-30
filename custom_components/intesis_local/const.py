"""Constants for the Intesis Local integration."""
from __future__ import annotations

from homeassistant.components.climate import (
    FAN_AUTO,
    FAN_HIGH,
    FAN_LOW,
    FAN_MEDIUM,
    SWING_OFF,
    SWING_ON,
    HVACMode,
)

DOMAIN = "intesis_local"

# Configuration
CONF_SCAN_INTERVAL = "scan_interval"
CONF_TEMP_STEP = "temp_step"

DEFAULT_SCAN_INTERVAL = 30
DEFAULT_TEMP_STEP = 0.5
DEFAULT_PORT = 80

# Datapoint UIDs
UID_POWER = 1
UID_MODE = 2
UID_FAN_SPEED = 4
UID_VANE_VERTICAL = 5
UID_VANE_HORIZONTAL = 6
UID_SETPOINT = 9
UID_CURRENT_TEMP = 10
UID_QUIET_MODE = 12  # 0=off, 1=quiet, 2=powerful
UID_TIMER = 13
UID_FILTER_STATUS = 14
UID_ERROR_CODE = 15
UID_MIN_TEMP = 35
UID_MAX_TEMP = 36

# API Commands
CMD_LOGIN = "login"
CMD_GET_INFO = "getinfo"
CMD_GET_DATAPOINTS = "getavailabledatapoints"
CMD_GET_DP_VALUE = "getdatapointvalue"
CMD_SET_DP_VALUE = "setdatapointvalue"

# HVAC Mode mappings (device value -> HA mode)
HVAC_MODE_MAP: dict[int, HVACMode] = {
    0: HVACMode.AUTO,
    1: HVACMode.COOL,
    2: HVACMode.HEAT,
    3: HVACMode.DRY,
    4: HVACMode.FAN_ONLY,
}

# Reverse mapping (HA mode -> device value)
HVAC_MODE_TO_DEVICE: dict[HVACMode, int] = {v: k for k, v in HVAC_MODE_MAP.items()}

# Fan mode mappings
FAN_MODE_MAP: dict[int, str] = {
    0: FAN_AUTO,
    1: FAN_LOW,
    2: "medium_low",
    3: FAN_MEDIUM,
    4: "medium_high",
    5: FAN_HIGH,
    6: "highest",
}

FAN_MODE_TO_DEVICE: dict[str, int] = {v: k for k, v in FAN_MODE_MAP.items()}

# Swing mode mappings for vertical vane
VANE_VERTICAL_MAP: dict[int, str] = {
    0: "position_1",
    1: "position_2",
    2: "position_3",
    3: "position_4",
    4: "position_5",
    10: SWING_ON,
}

VANE_VERTICAL_TO_DEVICE: dict[str, int] = {v: k for k, v in VANE_VERTICAL_MAP.items()}

# Swing mode mappings for horizontal vane
VANE_HORIZONTAL_MAP: dict[int, str] = {
    0: "position_1",
    1: "position_2",
    2: "position_3",
    3: "position_4",
    4: "position_5",
    5: "position_6",
    10: SWING_ON,
}

VANE_HORIZONTAL_TO_DEVICE: dict[str, int] = {v: k for k, v in VANE_HORIZONTAL_MAP.items()}

# Preset modes (UID 12)
# Using "eco" instead of "quiet" for Google Assistant compatibility
PRESET_MODE_MAP: dict[int, str] = {
    0: "none",
    1: "eco",  # Quiet mode - maps to Google Assistant "eco"
    2: "boost",  # Powerful mode
}

PRESET_MODE_TO_DEVICE: dict[str, int] = {v: k for k, v in PRESET_MODE_MAP.items()}

# Platforms to set up
PLATFORMS: list[str] = ["climate", "sensor", "binary_sensor"]
