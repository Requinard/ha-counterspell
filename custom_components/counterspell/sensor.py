"""Sensor platform for Counterspell."""
from __future__ import annotations

from datetime import datetime, timedelta
import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ATTR_ENTITY_ID,
    CONF_NAME,
    EntityCategory,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant, callback, Event
from homeassistant.helpers import entity_registry as er, device_registry as dr
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import (
    async_track_state_change_event,
    async_track_template_result,
    async_track_time_interval,
    TrackTemplate,
)
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.template import Template
from homeassistant.util import dt as dt_util

from .const import (
    DOMAIN,
    CONF_SOURCE_BINARY_SENSOR,
    CONF_SOURCE_TEMPLATE,
    CONF_PERIODS,
    PERIOD_TOTAL,
    PERIOD_DAILY,
    PERIOD_WEEKLY,
    PERIOD_MONTHLY,
    PERIOD_YEARLY,
)

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Counterspell sensors."""
    config = entry.data
    name = config[CONF_NAME]
    periods = config[CONF_PERIODS]
    source_binary_sensor = config.get(CONF_SOURCE_BINARY_SENSOR)
    source_template = config.get(CONF_SOURCE_TEMPLATE)

    device_info = None
    if source_binary_sensor:
        ent_reg = er.async_get(hass)
        source_entry = ent_reg.async_get(source_binary_sensor)
        if source_entry and source_entry.device_id:
            dev_reg = dr.async_get(hass)
            device = dev_reg.async_get(source_entry.device_id)
            if device:
                device_info = DeviceInfo(
                    identifiers=device.identifiers,
                )

    entities = []
    for period in periods:
        entities.append(
            CounterspellSensor(
                hass, entry, name, period, "count", device_info, source_binary_sensor, source_template
            )
        )
        entities.append(
            CounterspellSensor(
                hass, entry, name, period, "duration", device_info, source_binary_sensor, source_template
            )
        )

    async_add_entities(entities)

class CounterspellSensor(RestoreEntity, SensorEntity):
    """A Counterspell sensor."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        name: str,
        period: str,
        measure_type: str,
        device_info: DeviceInfo | None,
        source_binary_sensor: str | None,
        source_template: str | None,
    ) -> None:
        """Initialize the sensor."""
        self.hass = hass
        self._entry = entry
        self._base_name = name
        self._period = period
        self._measure_type = measure_type
        self._source_binary_sensor = source_binary_sensor
        self._source_template = source_template
        
        self._attr_name = f"{period.capitalize()} {measure_type.capitalize()}"
        self._attr_unique_id = f"{entry.entry_id}_{period}_{measure_type}"
        self._attr_device_info = device_info or DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=name,
        )
        
        if measure_type == "count":
            self._attr_state_class = SensorStateClass.TOTAL_INCREASING
            self._attr_icon = "mdi:counter"
        else:
            self._attr_device_class = SensorDeviceClass.DURATION
            self._attr_native_unit_of_measurement = UnitOfTime.SECONDS
            self._attr_state_class = SensorStateClass.TOTAL_INCREASING
            self._attr_icon = "mdi:timer-outline"

        self._state = 0.0
        self._last_reset = dt_util.now()
        self._active = False
        self._active_since: datetime | None = None
        self._template: Template | None = None

    async def async_added_to_hass(self) -> None:
        """Handle entity which will be added."""
        await super().async_added_to_hass()
        state = await self.async_get_last_state()
        if state:
            try:
                self._state = float(state.state)
            except ValueError:
                self._state = 0.0
            
            last_reset = state.attributes.get("last_reset")
            if last_reset:
                self._last_reset = dt_util.parse_datetime(last_reset) or dt_util.now()

        if self._source_binary_sensor:
            self.async_on_remove(
                async_track_state_change_event(
                    self.hass, [self._source_binary_sensor], self._async_on_state_change
                )
            )
            # Initial state
            curr_state = self.hass.states.get(self._source_binary_sensor)
            if curr_state:
                self._update_activity(curr_state.state == "on")
        elif self._source_template:
            self._template = Template(self._source_template, self.hass)
            self.async_on_remove(
                async_track_template_result(
                    self.hass,
                    [TrackTemplate(self._template, None)],
                    self._async_on_template_change,
                )
            )
            # Initial state
            try:
                self._update_activity(bool(self._template.async_render()))
            except Exception:
                _LOGGER.warning("Could not render template %s", self._source_template)

        if self._measure_type == "duration":
            self.async_on_remove(
                async_track_time_interval(self.hass, self._async_periodic_update, timedelta(minutes=1))
            )

    @callback
    def _async_periodic_update(self, now: datetime) -> None:
        """Periodic update for duration sensors."""
        if self._active:
            self._check_reset(now)
            self.async_write_ha_state()

    @callback
    def _async_on_state_change(self, event: Event) -> None:
        """Handle source state change."""
        new_state = event.data.get("new_state")
        if new_state:
            self._update_activity(new_state.state == "on")

    @callback
    def _async_on_template_change(self, event: Event, updates: list) -> None:
        """Handle template change."""
        result = updates[0].result
        self._update_activity(bool(result))

    def _update_activity(self, active: bool) -> None:
        """Update sensor activity."""
        now = dt_util.now()
        self._check_reset(now)

        if active and not self._active:
            # Became active
            if self._measure_type == "count":
                self._state += 1
            self._active_since = now
            self._active = True
            self.async_write_ha_state()
        elif not active and self._active:
            # Became inactive
            if self._measure_type == "duration" and self._active_since:
                self._state += (now - self._active_since).total_seconds()
            self._active = False
            self._active_since = None
            self.async_write_ha_state()

    def _check_reset(self, now: datetime) -> None:
        """Check if the sensor needs to be reset."""
        if self._period == PERIOD_TOTAL:
            return

        should_reset = False
        if self._period == PERIOD_DAILY:
            should_reset = now.date() > self._last_reset.date()
        elif self._period == PERIOD_WEEKLY:
            should_reset = now.isocalendar()[1] != self._last_reset.isocalendar()[1] or now.year != self._last_reset.year
        elif self._period == PERIOD_MONTHLY:
            should_reset = now.month != self._last_reset.month or now.year != self._last_reset.year
        elif self._period == PERIOD_YEARLY:
            should_reset = now.year != self._last_reset.year

        if should_reset:
            if self._active and self._measure_type == "duration" and self._active_since:
                # Add duration up to midnight if we really wanted to be precise, 
                # but for simplicity we reset and start fresh.
                pass
            self._state = 0.0
            self._last_reset = now
            if self._active:
                self._active_since = now
                if self._measure_type == "count":
                    self._state = 1 # It's active, so it counts as 1 in the new period

    @property
    def native_value(self) -> float:
        """Return the state of the sensor."""
        if self._active and self._measure_type == "duration" and self._active_since:
            # Return current state + duration since active
            now = dt_util.now()
            self._check_reset(now)
            return self._state + (now - self._active_since).total_seconds()
        return self._state

    @property
    def extra_state_attributes(self) -> dict:
        """Return extra state attributes."""
        return {
            "last_reset": self._last_reset.isoformat(),
            "period": self._period,
            "active": self._active,
        }
