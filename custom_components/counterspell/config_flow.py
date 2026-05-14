"""Config flow for Counterspell integration."""
from __future__ import annotations

from typing import Any
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_NAME, CONF_DEVICE_ID
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

    def __init__(self) -> None:
        """Initialize flow."""
        self._data: dict[str, Any] = {}
        self._reconfigure_entry: config_entries.ConfigEntry | None = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        return self.async_show_menu(
            step_id="user",
            menu_options=["binary_sensor", "template"],
        )

    async def async_step_binary_sensor(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle binary sensor source."""
        if user_input is not None:
            self._data.update(user_input)
            # Auto-generate name
            entity_id = user_input[CONF_SOURCE_BINARY_SENSOR]
            state = self.hass.states.get(entity_id)
            self._data[CONF_NAME] = state.name if state else entity_id
            return await self.async_step_periods()

        return self.async_show_form(
            step_id="binary_sensor",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_SOURCE_BINARY_SENSOR): selector.EntitySelector(
                        selector.EntitySelectorConfig(domain="binary_sensor")
                    ),
                }
            ),
        )

    async def async_step_template(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle template source."""
        if user_input is not None:
            self._data.update(user_input)
            return await self.async_step_periods()

        return self.async_show_form(
            step_id="template",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_SOURCE_TEMPLATE): selector.TemplateSelector(),
                    vol.Required(CONF_NAME): selector.TextSelector(),
                    vol.Optional(CONF_DEVICE_ID): selector.DeviceSelector(),
                }
            ),
        )

    async def async_step_periods(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle period selection."""
        if user_input is not None:
            self._data.update(user_input)
            if self._reconfigure_entry:
                return self.async_update_reload_and_abort(
                    self._reconfigure_entry, data=self._data
                )
            return self.async_create_entry(title=self._data[CONF_NAME], data=self._data)

        suggested_values = self._data.get(CONF_PERIODS, PERIODS)
        if self._reconfigure_entry:
            suggested_values = self._reconfigure_entry.data.get(CONF_PERIODS, PERIODS)

        return self.async_show_form(
            step_id="periods",
            data_schema=self.add_suggested_values_to_schema(
                vol.Schema(
                    {
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
                {CONF_PERIODS: suggested_values},
            ),
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle reconfiguration."""
        self._reconfigure_entry = self.hass.config_entries.async_get_entry(
            self.context["entry_id"]
        )
        self._data = dict(self._reconfigure_entry.data)
        return await self.async_step_periods()
