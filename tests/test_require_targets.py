"""Tests for require_targets on HomeKit bridges."""

from unittest.mock import Mock

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.homekit import HOMEKIT_FILTER_SCHEMA, HomeKit
from custom_components.homekit.const import (
    CONF_REQUIRE_TARGETS,
    DOMAIN,
    HOMEKIT_MODE_BRIDGE,
)
from homeassistant.const import ATTR_AREA_ID, ATTR_LABEL_ID
from homeassistant.core import HomeAssistant
from homeassistant.helpers import (
    area_registry as ar,
    device_registry as dr,
    entity_registry as er,
    label_registry as lr,
)
from homeassistant.helpers.entityfilter import FILTER_SCHEMA


def _mock_homekit(
    hass: HomeAssistant,
    entry: MockConfigEntry,
    include_targets: dict[str, list[str]],
    require_targets: dict[str, list[str]],
) -> HomeKit:
    homekit = HomeKit(
        hass=hass,
        name="HASS Bridge",
        port=21063,
        ip_address=None,
        entity_filter=FILTER_SCHEMA({}),
        exclude_accessory_mode=False,
        entity_config={},
        homekit_mode=HOMEKIT_MODE_BRIDGE,
        include_targets=include_targets,
        exclude_targets={},
        advertise_ips=[],
        entry_id=entry.entry_id,
        entry_title=entry.title,
        require_targets=require_targets,
    )
    homekit.bridge = Mock(accessories={})
    return homekit


def _create_entity(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    entity_id: str,
    *,
    area_id: str | None = None,
    device_id: str | None = None,
    labels: set[str] | None = None,
) -> None:
    domain, object_id = entity_id.split(".")
    entry = entity_registry.async_get_or_create(
        domain, "test", object_id, suggested_object_id=object_id, device_id=device_id
    )
    entity_registry.async_update_entity(
        entry.entity_id, area_id=area_id, labels=labels or set()
    )
    hass.states.async_set(entity_id, "on")


def test_schema_accepts_require_targets() -> None:
    """Test require_targets validates like the other target filters."""
    config = HOMEKIT_FILTER_SCHEMA({CONF_REQUIRE_TARGETS: {ATTR_LABEL_ID: "homekit"}})
    assert config[CONF_REQUIRE_TARGETS] == {ATTR_LABEL_ID: ["homekit"]}
    assert HOMEKIT_FILTER_SCHEMA({})[CONF_REQUIRE_TARGETS] == {}


async def test_require_targets_limits_area_to_label(
    hass: HomeAssistant,
    area_registry: ar.AreaRegistry,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    label_registry: lr.LabelRegistry,
) -> None:
    """Test a bridge per area only exposes entities that also have the label."""
    entry = MockConfigEntry(domain=DOMAIN, title="Living Room")
    entry.add_to_hass(hass)
    living_room = area_registry.async_create("Living Room")
    kitchen = area_registry.async_create("Kitchen")
    homekit_label = label_registry.async_create("HomeKit")

    hue_device = device_registry.async_get_or_create(
        config_entry_id=entry.entry_id, identifiers={("test", "hue-bulb")}
    )
    device_registry.async_update_device(
        hue_device.id,
        area_id=living_room.id,
        labels={homekit_label.label_id},
    )

    _create_entity(
        hass,
        entity_registry,
        "light.living_room_lamp",
        area_id=living_room.id,
        labels={homekit_label.label_id},
    )
    _create_entity(
        hass, entity_registry, "light.living_room_unlabeled", area_id=living_room.id
    )
    _create_entity(
        hass,
        entity_registry,
        "light.kitchen_lamp",
        area_id=kitchen.id,
        labels={homekit_label.label_id},
    )
    _create_entity(
        hass, entity_registry, "light.living_room_hue_bulb", device_id=hue_device.id
    )
    hass.states.async_set("light.no_registry_entry", "on")

    homekit = _mock_homekit(
        hass,
        entry,
        include_targets={ATTR_AREA_ID: [living_room.id]},
        require_targets={ATTR_LABEL_ID: [homekit_label.label_id]},
    )
    assert {
        state.entity_id for state in await homekit.async_configure_accessories()
    } == {"light.living_room_lamp", "light.living_room_hue_bulb"}

    # Without require_targets the whole area is exposed
    homekit = _mock_homekit(
        hass, entry, include_targets={ATTR_AREA_ID: [living_room.id]}, require_targets={}
    )
    assert {
        state.entity_id for state in await homekit.async_configure_accessories()
    } == {
        "light.living_room_lamp",
        "light.living_room_unlabeled",
        "light.living_room_hue_bulb",
    }

    # require_targets on its own exposes everything with the label
    homekit = _mock_homekit(
        hass,
        entry,
        include_targets={},
        require_targets={ATTR_LABEL_ID: [homekit_label.label_id]},
    )
    assert {
        state.entity_id for state in await homekit.async_configure_accessories()
    } == {"light.living_room_lamp", "light.kitchen_lamp", "light.living_room_hue_bulb"}
