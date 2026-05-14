"""Test Counterspell sensors."""
from datetime import timedelta
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import STATE_ON, STATE_OFF, EntityCategory
from homeassistant.helpers import entity_registry as er
from homeassistant.util import dt as dt_util

from custom_components.counterspell.const import DOMAIN

async def test_sensors(hass: HomeAssistant, freezer) -> None:
    """Test sensor behavior."""
    now = dt_util.now()
    freezer.move_to(now)

    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            "name": "Test Counter",
            "source_binary_sensor": "binary_sensor.test_source",
            "periods": ["total"],
        },
        entry_id="test_entry",
    )
    entry.add_to_hass(hass)
    
    # Initialize the source sensor
    hass.states.async_set("binary_sensor.test_source", STATE_OFF)
    
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    # Entities created: total count and total duration
    count_entity_id = "sensor.test_counter_total_count"
    duration_entity_id = "sensor.test_counter_total_active_duration"
    
    assert float(hass.states.get(count_entity_id).state) == 0.0
    assert float(hass.states.get(duration_entity_id).state) == 0.0
    
    # Check friendly name
    assert hass.states.get(count_entity_id).attributes.get("friendly_name") == "Test Counter Total Count"
    assert hass.states.get(duration_entity_id).attributes.get("friendly_name") == "Test Counter Total Active Duration"

    # Check entity category
    ent_reg = er.async_get(hass)
    reg_entry = ent_reg.async_get(count_entity_id)
    assert reg_entry.entity_category == EntityCategory.DIAGNOSTIC
    reg_entry = ent_reg.async_get(duration_entity_id)
    assert reg_entry.entity_category == EntityCategory.DIAGNOSTIC

    # Turn it on
    hass.states.async_set("binary_sensor.test_source", STATE_ON)
    await hass.async_block_till_done()

    # Count should be 1
    assert float(hass.states.get(count_entity_id).state) == 1.0
    
    # Wait 10 seconds
    freezer.tick(timedelta(seconds=10))
    
    hass.states.async_set("binary_sensor.test_source", STATE_OFF)
    await hass.async_block_till_done()

    # Duration should be 10
    assert float(hass.states.get(duration_entity_id).state) == 10.0
    # Count should still be 1
    assert float(hass.states.get(count_entity_id).state) == 1.0

    # Turn it on again
    hass.states.async_set("binary_sensor.test_source", STATE_ON)
    await hass.async_block_till_done()
    
    # Count should be 2
    assert float(hass.states.get(count_entity_id).state) == 2.0

async def test_template_sensor(hass: HomeAssistant) -> None:
    """Test sensor behavior with template source."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            "name": "Template Counter",
            "source_template": "{{ is_state('input_boolean.test', 'on') }}",
            "periods": ["total"],
        },
        entry_id="test_entry_template",
    )
    entry.add_to_hass(hass)
    
    hass.states.async_set("input_boolean.test", STATE_OFF)
    
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    count_entity_id = "sensor.template_counter_total_count"
    
    assert float(hass.states.get(count_entity_id).state) == 0.0

    # Turn it on
    hass.states.async_set("input_boolean.test", STATE_ON)
    await hass.async_block_till_done()

    # Count should be 1
    assert float(hass.states.get(count_entity_id).state) == 1.0

async def test_period_reset(hass: HomeAssistant, freezer) -> None:
    """Test sensor behavior with daily reset."""
    now = dt_util.now().replace(hour=23, minute=59, second=50)
    freezer.move_to(now)

    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            "name": "Daily Counter",
            "source_binary_sensor": "binary_sensor.test_source",
            "periods": ["daily"],
        },
        entry_id="test_entry_daily",
    )
    entry.add_to_hass(hass)
    
    hass.states.async_set("binary_sensor.test_source", STATE_OFF)
    
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    count_entity_id = "sensor.daily_counter_count_today"
    
    # Turn it on
    hass.states.async_set("binary_sensor.test_source", STATE_ON)
    await hass.async_block_till_done()
    assert float(hass.states.get(count_entity_id).state) == 1.0

    # Move to next day
    freezer.tick(timedelta(seconds=20))
    
    # State should still be 1 because it's still ON and it was active during transition
    assert float(hass.states.get(count_entity_id).state) == 1.0
    
    # Turn it off
    hass.states.async_set("binary_sensor.test_source", STATE_OFF)
    await hass.async_block_till_done()
    assert float(hass.states.get(count_entity_id).state) == 1.0
    
    # Turn it on again (second time today)
    hass.states.async_set("binary_sensor.test_source", STATE_ON)
    await hass.async_block_till_done()
    assert float(hass.states.get(count_entity_id).state) == 2.0
