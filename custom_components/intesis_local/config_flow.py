"""Config flow for Intesis Local integration."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .api import IntesisAuthError, IntesisConnectionError, IntesisLocalAPI
from .const import (
    CONF_SCAN_INTERVAL,
    CONF_TEMP_STEP,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_TEMP_STEP,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_USERNAME, default="admin"): str,
        vol.Required(CONF_PASSWORD, default="admin"): str,
    }
)


class IntesisLocalConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Intesis Local."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                # Create session and validate connection
                async with aiohttp.ClientSession() as session:
                    api = IntesisLocalAPI(
                        host=user_input[CONF_HOST],
                        username=user_input[CONF_USERNAME],
                        password=user_input[CONF_PASSWORD],
                        session=session,
                    )
                    device_info = await api.validate_connection()

                # Extract serial for unique ID
                serial = device_info.get("sn", "unknown").split(" / ")[0]
                model = device_info.get("deviceModel", "Unknown")

                await self.async_set_unique_id(serial)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=f"Intesis {model}",
                    data=user_input,
                )

            except IntesisAuthError:
                errors["base"] = "invalid_auth"
            except IntesisConnectionError:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Get the options flow for this handler."""
        return IntesisOptionsFlow(config_entry)


class IntesisOptionsFlow(OptionsFlow):
    """Handle options flow for Intesis Local."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current_interval = self.config_entry.options.get(
            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
        )
        current_temp_step = self.config_entry.options.get(
            CONF_TEMP_STEP, DEFAULT_TEMP_STEP
        )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_SCAN_INTERVAL,
                        default=current_interval,
                    ): vol.In(
                        {
                            10: "10 seconds",
                            30: "30 seconds (default)",
                            60: "60 seconds",
                        }
                    ),
                    vol.Optional(
                        CONF_TEMP_STEP,
                        default=current_temp_step,
                    ): vol.In(
                        {
                            0.5: "0.5°C (default)",
                            1.0: "1.0°C",
                        }
                    ),
                }
            ),
        )
