"""Test Counterspell config flow."""
from unittest.mock import patch

from homeassistant import config_entries, data_entry_flow
from homeassistant.core import HomeAssistant

from custom_components.counterspell.const import DOMAIN

async def test_flow_user_init(hass: HomeAssistant) -> None:
    """Test the user initiated flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "user"

    with patch(
        "custom_components.counterspell.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "name": "My Counter",
                "source_binary_sensor": "binary_sensor.test",
                "periods": ["daily", "total"],
            },
        )
        await hass.async_block_till_done()

    assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result["title"] == "My Counter"
    assert result["data"] == {
        "name": "My Counter",
        "source_binary_sensor": "binary_sensor.test",
        "periods": ["daily", "total"],
    }
    assert len(mock_setup_entry.mock_calls) == 1

async def test_flow_user_invalid_source(hass: HomeAssistant) -> None:
    """Test the user initiated flow with invalid source (neither sensor nor template)."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "name": "My Counter",
            "periods": ["daily"],
        },
    )
    
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["errors"] == {"base": "provide_source"}

async def test_flow_user_defaults(hass: HomeAssistant) -> None:
    """Test the user initiated flow has correct defaults."""
    from custom_components.counterspell.const import CONF_PERIODS, PERIODS
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    
    # Check defaults in the schema
    schema = result["data_schema"].schema
    
    periods_key = None
    for key in schema:
        if str(key) == CONF_PERIODS:
            periods_key = key
            break
    
    assert periods_key is not None
    assert periods_key.default() == PERIODS
    
    # Check suggested value (for the UI)
    suggested_value = None
    if hasattr(periods_key, "description") and isinstance(periods_key.description, dict):
        suggested_value = periods_key.description.get("suggested_value")
    
    assert suggested_value == PERIODS
    
    # Test that the schema applies the default
    # Note: binary_sensor and template are optional in the schema but checked in the code
    data = {"name": "Test"}
    processed_data = result["data_schema"](data)
    assert processed_data[CONF_PERIODS] == PERIODS
