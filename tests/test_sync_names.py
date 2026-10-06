"""Tests for syncing renamed entities to HomeKit."""

from unittest.mock import patch

import pytest

from custom_components.homekit.accessories import HomeAccessory, get_accessory
from homeassistant.components.light import ATTR_SUPPORTED_COLOR_MODES, ColorMode
from homeassistant.const import ATTR_FRIENDLY_NAME, CONF_NAME, STATE_ON
from homeassistant.core import HomeAssistant

ENTITY_ID = "light.kitchen_ceiling_lamp_1"
BASE_ATTRS = {ATTR_SUPPORTED_COLOR_MODES: [ColorMode.BRIGHTNESS], "brightness": 100}


async def _setup_accessory(hass: HomeAssistant, hk_driver, config: dict):
    hass.states.async_set(
        ENTITY_ID, STATE_ON, {**BASE_ATTRS, ATTR_FRIENDLY_NAME: "Old Name"}
    )
    await hass.async_block_till_done()
    acc = get_accessory(hass, hk_driver, hass.states.get(ENTITY_ID), 2, config)
    acc.run()
    await hass.async_block_till_done()
    return acc


@pytest.mark.parametrize(
    ("config", "expected_display_name", "expect_reload"),
    [
        ({}, "Old Name", True),
        ({CONF_NAME: "Pinned Name"}, "Pinned Name", False),
    ],
)
async def test_rename_reloads_accessory(
    hass: HomeAssistant, hk_driver, config, expected_display_name, expect_reload
) -> None:
    """Test a rename rebuilds the accessory unless the name is pinned."""
    acc = await _setup_accessory(hass, hk_driver, config)
    assert acc.display_name == expected_display_name

    with patch.object(HomeAccessory, "async_reload") as mock_reload:
        hass.states.async_set(
            ENTITY_ID, STATE_ON, {**BASE_ATTRS, ATTR_FRIENDLY_NAME: "New Name"}
        )
        await hass.async_block_till_done()
    assert mock_reload.called is expect_reload


async def test_state_change_without_rename_does_not_reload(
    hass: HomeAssistant, hk_driver
) -> None:
    """Test normal state updates do not rebuild the accessory."""
    await _setup_accessory(hass, hk_driver, {})

    with patch.object(HomeAccessory, "async_reload") as mock_reload:
        hass.states.async_set(
            ENTITY_ID,
            STATE_ON,
            {**BASE_ATTRS, "brightness": 200, ATTR_FRIENDLY_NAME: "Old Name"},
        )
        await hass.async_block_till_done()
    assert not mock_reload.called


async def test_new_accessory_uses_new_name(hass: HomeAssistant, hk_driver) -> None:
    """Test the rebuilt accessory takes the current entity name."""
    hass.states.async_set(
        ENTITY_ID, STATE_ON, {**BASE_ATTRS, ATTR_FRIENDLY_NAME: "New Name"}
    )
    acc = get_accessory(hass, hk_driver, hass.states.get(ENTITY_ID), 2, {})
    assert acc.display_name == "New Name"
