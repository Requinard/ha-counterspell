"""Test Counterspell config flow."""
from unittest.mock import patch
from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant import config_entries, data_entry_flow
from homeassistant.core import HomeAssistant

from custom_components.counterspell.const import DOMAIN

async def test_flow_binary_sensor(hass: HomeAssistant) -> None:
    """Test the flow starting with binary sensor."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == data_entry_flow.FlowResultType.MENU
    
    # Select binary_sensor
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"next_step_id": "binary_sensor"}
    )
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "binary_sensor"
    
    # Configure binary sensor
    hass.states.async_set("binary_sensor.test_motion", "off", {"friendly_name": "Test Motion"})
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"source_binary_sensor": "binary_sensor.test_motion"}
    )
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "periods"
    
    # Configure periods
    with patch("custom_components.counterspell.async_setup_entry", return_value=True):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"periods": ["daily"]}
        )
        await hass.async_block_till_done()
        
    assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result["title"] == "Test Motion"
    assert result["data"]["name"] == "Test Motion"
    assert result["data"]["source_binary_sensor"] == "binary_sensor.test_motion"
    assert result["data"]["periods"] == ["daily"]

async def test_flow_template(hass: HomeAssistant) -> None:
    """Test the flow starting with template."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    
    # Select template
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"next_step_id": "template"}
    )
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "template"
    
    # Configure template
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {
            "source_template": "{{ states('input_boolean.test') == 'on' }}",
            "name": "My Template",
        }
    )
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "periods"
    
    # Configure periods
    with patch("custom_components.counterspell.async_setup_entry", return_value=True):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"periods": ["daily", "weekly"]}
        )
        await hass.async_block_till_done()
        
    assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result["title"] == "My Template"
    assert result["data"]["name"] == "My Template"
    assert result["data"]["source_template"] == "{{ states('input_boolean.test') == 'on' }}"
    assert result["data"]["periods"] == ["daily", "weekly"]

async def test_reconfigure(hass: HomeAssistant) -> None:
    """Test reconfiguration."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            "name": "Old Name",
            "source_binary_sensor": "binary_sensor.old",
            "periods": ["total"],
        },
        entry_id="test_reconfigure",
    )
    entry.add_to_hass(hass)
    
    result = await hass.config_entries.flow.async_init(
        DOMAIN, 
        context={"source": config_entries.SOURCE_RECONFIGURE, "entry_id": entry.entry_id},
    )
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "periods"
    
    # Update periods
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"periods": ["daily", "total"]}
    )
    await hass.async_block_till_done()
    
    assert result["type"] == data_entry_flow.FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert entry.data["periods"] == ["daily", "total"]

async def test_flow_template_with_device(hass: HomeAssistant) -> None:
    """Test the flow starting with template and selecting a device."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    
    # Select template
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"next_step_id": "template"}
    )
    
    # Configure template with device
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {
            "source_template": "{{ true }}",
            "name": "Device Template",
            "device_id": "test_device_id",
        }
    )
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "periods"
    
    # Configure periods
    with patch("custom_components.counterspell.async_setup_entry", return_value=True):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"periods": ["total"]}
        )
        await hass.async_block_till_done()
        
    assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result["data"]["device_id"] == "test_device_id"
