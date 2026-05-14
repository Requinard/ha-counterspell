"""Config flow for Counterspell integration."""
from __future__ import annotations

from typing import Any
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector

from .const import (
    DOMAIN,
    CONF_SOURCE_BINARY_SENSOR,
    CONF_SOURCE_TEMPLATE,
    CONF_PERIODS,
    PERIODS,
)

class CounterspellConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Counterspell."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            if not user_input.get(CONF_SOURCE_BINARY_SENSOR) and not user_input.get(CONF_SOURCE_TEMPLATE):
                errors["base"] = "provide_source"
            else:
                return self.async_create_entry(title=user_input[CONF_NAME], data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_NAME): str,
                    vol.Optional(CONF_SOURCE_BINARY_SENSOR): selector.EntitySelector(
                        selector.EntitySelectorConfig(domain="binary_sensor")
                    ),
                    vol.Optional(CONF_SOURCE_TEMPLATE): selector.TemplateSelector(),
                    vol.Required(CONF_PERIODS, default=PERIODS): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=PERIODS,
                            multiple=True,
                            mode=selector.SelectSelectorMode.LIST,
                            translation_key="periods",
                        )
                    ),
                }
            ),
            errors=errors,
        )
